# filename: schemas/agent_io_reference.md
## StoryVideoGenerator — Scenario Inputs/Outputs (Agent용)
- Inputs:
  - language (ko|ja, optional)
  - min_score (number, optional)
  - status ("new"| "any", optional)
- Outputs(JSON):
```json
{
  "story_id": "EP0001",
  "title": "일본인 아내의 굿즈 사건",
  "audio_url": "https://drive.google.com/..",
  "image_url": "https://...",
  "video_url_temp": "https://cloudconvert.com/..",
  "youtube_watch_url": "https://youtu.be/XXXX"
}
