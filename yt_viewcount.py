import argparse
import json
import pickle
import time
import urllib
from datetime import datetime
from io import BytesIO
from os import fsync

import h5py
import numpy as np
import pycurl


ALBUMS = 'PATH TO album_lens.pkl'
SONGS = 'PATH TO msd_summary_file.h5' # https://labrosa.ee.columbia.edu/millionsong/sites/default/files/AdditionalFiles/msd_summary_file.h5
YT_API_KEY = 'YOUR_KEY_HERE'
YT_API_URL = 'https://www.googleapis.com/youtube/v3/'


def main():
    parser = argparse.ArgumentParser(
        description='Youtube view-count crawler for MSD')
    parser.add_argument(
        '-i', '--songs',
        help='*.h5 (album_name, artist_name, song_title)', default=SONGS)
    parser.add_argument(
        '-a', '--albums',
        help='*.pkl; dict[album_len] = [song_id,...]', default=ALBUMS)
    parser.add_argument('-o', '--output', help='YT view-count', required=True)
    parser.add_argument(
        '-s', '--album-size', default=2)
    parser.add_argument(
        '-b', '--begin-at', help='Beginning index (zero-based)', required=True)
    parser.add_argument(
        '-e', '--end-at', help='Ending index (zero-based)', required=True)
    parser.add_argument(
        '-k', '--yt_key', default=YT_API_KEY)

    args = parser.parse_args()
    h5f = args.songs
    albums_f = args.albums
    output = args.output
    a_size = int(args.album_size)
    begin_at = int(args.begin_at)
    end_at = int(args.end_at)
    yt_key = args.yt_key

    h5 = h5py.File(h5f, 'r')
    songs_m = h5['metadata']['songs']
    songs_a = h5['analysis']['songs']
    albums = None
    with open(albums_f, 'rb') as handle:
        albums = pickle.load(handle)

    v_countss = []
    tidss = []
    uptimess = []
    flog = open('{}.log'.format(output), 'w')
    if a_size not in albums:
        print ('No album with size {:d}.'.format(a_size))
        return

    for album in albums[a_size][begin_at:end_at + 1]:
        v_counts = []
        tids = []
        uptimes = []
        for sid in album:
            song = songs_m[sid]
            tid = songs_a[sid]['track_id'].decode('utf8')
            tids.append(tid)
            artist_name = \
                song['artist_name'].decode('utf8').replace(' ', '+')
            song_title_orig = song['title'].decode('utf8')
            song_title = song_title_orig.replace(' ', '+')
            # TODO: YT search query
            query = '{}+{}'.format(artist_name, song_title)

            curl_s = pycurl.Curl()
            buf_s = BytesIO()
            params_s = {
                'q': query, 'part': 'snippet', 'type': 'video',
                'key': yt_key, }
            curl_s.setopt(
                curl_s.URL, '{}search?{}'.format(
                    YT_API_URL, urllib.parse.urlencode(params_s)))
            curl_s.setopt(curl_s.WRITEDATA, buf_s)
            s_success = True
            try:
                curl_s.perform()
            except pycurl.error:
                s_success = False
            status_s = curl_s.getinfo(curl_s.RESPONSE_CODE)
            if status_s == 200 and s_success:  # success
                # print ("search success")
                result_s = json.loads(buf_s.getvalue().decode('utf8'))
                ids = ''
                for res in result_s['items']:
                    res_id = res['id']
                    if res_id['kind'] == 'youtube#video':
                        title = res['snippet']['title']

                        # # #
                        #
                        #  TODO: this part checks if res_id's song is a
                        #        correct YT search result.
                        #

                        if song_title_orig.lower() in title.lower():
                            ids += res_id['videoId']
                            ids += ','

                        # # #

                if ids == '':
                    flog.write(
                        '{}.mp3: '.format(tid) +
                        'no results. candidates are: ')
                    for res in result_s['items']:
                        flog.write('{}; '.format(res['snippet']['title']))
                    flog.write('Search target is {}.\n'.format(query))
                    v_counts.append(0)
                    uptimes.append(None)
                else:
                    curl_vc = pycurl.Curl()
                    buf_vc = BytesIO()
                    params_vc = {
                        'part': 'snippet,statistics',
                        'id': ids, 'key': yt_key}
                    curl_vc.setopt(
                        curl_vc.URL, '{}videos?{}'.format(
                            YT_API_URL, urllib.parse.urlencode(params_vc)))
                    curl_vc.setopt(curl_vc.WRITEDATA, buf_vc)
                    vc_success = True
                    try:
                        curl_vc.perform()
                    except pycurl.error:
                        vc_success = False
                    status_vc = curl_vc.getinfo(curl_vc.RESPONSE_CODE)
                    if status_vc == 200 and vc_success:
                        result_vc = json.loads(
                            buf_vc.getvalue().decode('utf8'))
                        mvc = 0  # maximum view-count
                        uptime = None
                        for res in result_vc['items']:
                            vc = int(res['statistics']['viewCount'])
                            if vc > mvc:
                                mvc = vc
                                upt = res['snippet']['publishedAt']
                                d = datetime.strptime(
                                    upt, '%Y-%m-%dT%H:%M:%S.000Z')
                                uptime = time.mktime(d.timetuple())
                        v_counts.append(mvc)
                        uptimes.append(uptime)
                    else:
                        v_counts.append(0)
                        uptimes.append(None)
                        flog.write(
                            '{}.mp3 ERROR getting view-count: '.format(
                                tid) +
                            'status {:d}\n'.format(status_vc))

            else:
                v_counts.append(0)
                uptimes.append(None)
                flog.write(
                    '{}.mp3 ERROR searching video: '.format(tid) +
                    'status {:d}\n'.format(status_s))

            flog.flush()
            fsync(flog.fileno())

        tidss.append(tids)
        v_countss.append(v_counts)
        uptimess.append(uptimes)
        np.save('{}.tids'.format(output), np.array(tidss))
        np.save('{}.vc'.format(output), np.array(v_countss))
        np.save('{}.upt'.format(output), np.array(uptimess))

    h5.close()
    flog.close()


if __name__ == '__main__':
    main()
