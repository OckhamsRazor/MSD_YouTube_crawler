# MSD-YouTube Crawler
A crawler to fetch YouTube view-counts for the Million Song Dataset (MSD).
`\*.npy` files for now are crawled data of songs from albums with size 5, i.e., `album_lens[5]`, which include 10,285 albums and 51,425 (10,285\*5) songs.

In the cleaned version considering YouTube view-counts availability (`track_id_by_alb.npy`), there are 7,807 albums and 31,562 songs. In another cleaned version further considering album release time (from MSD), there are 3,384 albums and 13,648 songs [details](https://docs.google.com/presentation/d/1VLGojgyecFJZFui7-MGZDivSfUBuewQIlMK4v4_po2s/edit?usp=sharing).

## Prerequisites
1. Download the MSD summary file from [Here](https://labrosa.ee.columbia.edu/millionsong/sites/default/files/AdditionalFiles/msd_summary_file.h5).
2. Set the constants `ALBUMS, SONGS, YT_API_KEY` in `yt_viewcount.py` to corresponding values.
   - ALBUMS: path to the file `album_lens.pkl`.
   - SONGS: path to the MSD summary file (prerequisite 1).
   - YT_API_KEY: your own YouTube API key.

## Files
- yt_viewcount.py
  - The crawler. Please refer to ArgumentParser and TODOs in this file for further information.
- raw/
  - yt_view_count.npy
    - Size: (10285, 5)
    - Highest YouTube view-count from search results for each song.
  - upload_time.npy
    - Size: (10285, 5)
    - The time span (months) each song uploaded to YouTube.
  - track_ids.npy
    - Size: (10285, 5)
    - Echo Nest track ID for each song.
  - track_id_by_alb.npy
    - Size: (7807, 2~5)
    - Excluded songs with zero/unknown view-counts, and then albums with fewer than two songs.
    -
- track_ids.npy
  - Size: (31562,)
  - Flattened version of `raw/track_id_by_alb.npy`.
- album_lens.pkl
  - A python dictionary: `album_lens[album_len] = [song_id,...]`, which groups songs in same albums (of same size) together. The song_id is from `msd_summary_file.h5`, which can be seen as a list of songs with size 1,000,000.
  - For example, `album_lens[5]` is a list of lists with size 5, i.e., albums with size 5.
- (ytr/yva/yte).npy
  - Size: 25375/3109/3078 (Sum: 31562)
  - YouTube view-counts.
- (albs_tr_5/albs_va_5/albs_te_5).npy
  - Size: 6247/780/780 (Sum: 7807)
  - Example
    - `albs_tr_5[0] = [0, 1]`, then `ytr[0]` and `ytr[1]` are YouTube view-counts of songs from the same album.
    - `track_ids[0]` and `track_ids[1]` are their corresponding Echo Nest track IDs.
- (valid_albs_tr_5/valid_albs_va_5/valid_albs_te_5).npy
  - Size: 2721/329/334 (Sum: 3384)
  - Further cleaned version of (albs_tr_5/albs_va_5/albs_te_5).npy
  - Excluded albums with songs with different release time (according to MSD).
