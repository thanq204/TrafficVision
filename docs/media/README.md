# TrafficVision demo

The demo is derived from **Street traffic** by **Editor**. The source is licensed under [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). The annotated video, GIF and still in this directory are distributed under the same terms. [Wikimedia Commons source](https://commons.wikimedia.org/wiki/File:Street_traffic.webm) · [Original video](https://www.youtube.com/watch?v=_7sCYyxw4Ic) · [Author](https://www.youtube.com/user/Editor)

We clipped the first 12 seconds, resized to 768 × 432, converted to 20 FPS, removed audio, and added track boxes, IDs and line-crossing totals with the CLI. See [summary.json](summary.json) for the generated report. The video shows model outputs on an unlabeled clip.

## Reproduce

From the repo root, install the requirements and download the original WebM to `data/street_traffic.webm`. FFmpeg is used to prepare the clip and convert the AVI for browser playback.

```bash
ffmpeg -y -i data/street_traffic.webm -t 12 -an -vf "scale=768:432,fps=20" -c:v libx264 -pix_fmt yuv420p data/east.mp4
python main.py --source data/east.mp4 --headless --device cpu --output data/portfolio.avi --summary data/portfolio.json
ffmpeg -y -i data/portfolio.avi -an -c:v libx264 -crf 24 -pix_fmt yuv420p -movflags +faststart docs/media/traffic-demo.mp4
ffmpeg -y -ss 5 -i docs/media/traffic-demo.mp4 -frames:v 1 -update 1 docs/media/traffic-preview.jpg
ffmpeg -y -i docs/media/traffic-demo.mp4 -vf "fps=6,scale=400:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer" -loop 0 docs/media/traffic-demo.gif
```

Verified on Windows CPU with Python 3.11.15, torch 2.5.1+cpu, torchvision 0.20.1+cpu, Ultralytics 8.0.200, DeepSORT Realtime 1.3.2 and OpenCV 4.10.0.84. The 240 decoded frames match the report. Playback duration does not measure inference latency.
