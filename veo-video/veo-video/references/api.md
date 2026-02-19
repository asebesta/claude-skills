# Veo 3.1 API Reference

## Parameters

| Parameter | Type | Values | Notes |
|-----------|------|--------|-------|
| `prompt` | string | Any text | Required. Supports dialogue in quotes, SFX descriptions, ambient audio cues. |
| `negativePrompt` | string | Descriptive terms | Elements to exclude from generation. |
| `image` | Image object | `{ imageBytes, mimeType }` | Starting frame for image-to-video or interpolation. |
| `lastFrame` | Image object | `{ imageBytes, mimeType }` | End frame for interpolation. Requires `image` to also be set. Set in `config`. |
| `referenceImages` | array | Up to 3 entries | Each: `{ image, referenceType: "asset" }`. Set in `config`. |
| `video` | Video object | Previous Veo output | For video extension only. |
| `aspectRatio` | string | `"16:9"` (default), `"9:16"` | Set in `config`. |
| `resolution` | string | `"720p"` (default), `"1080p"`, `"4k"` | Set in `config`. 1080p/4k require 8s duration. Extension is 720p only. |
| `durationSeconds` | string | `"4"`, `"6"`, `"8"` | Set in `config`. Must be `"8"` for extension, references, 1080p, 4k. |
| `numberOfVideos` | integer | Typically 1 | Set in `config`. Used with extension. |
| `personGeneration` | string | `"allow_all"` (text-to-video), `"allow_adult"` (image/interpolation/references) | Set in `config`. Regional restrictions apply (EU/UK/CH/MENA). |
| `seed` | integer | Any number | Set in `config`. Improves consistency across generations. |

## SDK Methods

### `ai.models.generateVideos(options)`
Starts video generation. Returns an operation object.

```typescript
{
  model: string;          // "veo-3.1-generate-preview"
  prompt: string;
  image?: { imageBytes: string; mimeType: string };
  video?: VideoObject;    // from previous operation
  config?: {
    aspectRatio?: "16:9" | "9:16";
    resolution?: "720p" | "1080p" | "4k";
    durationSeconds?: "4" | "6" | "8";
    negativePrompt?: string;
    numberOfVideos?: number;
    personGeneration?: "allow_all" | "allow_adult";
    seed?: number;
    lastFrame?: { imageBytes: string; mimeType: string };
    referenceImages?: Array<{ image: ImageObject; referenceType: "asset" }>;
  };
}
```

### `ai.operations.getVideosOperation({ operation })`
Polls operation status. Returns updated operation with `done` boolean.

### `ai.files.download({ file, downloadPath })`
Downloads a generated video to local filesystem.

- `file`: `operation.response.generatedVideos[0].video`
- `downloadPath`: local file path (e.g. `"output.mp4"`)

## REST API

Base URL: `https://generativelanguage.googleapis.com/v1beta`

### Generate
```
POST /models/veo-3.1-generate-preview:predictLongRunning
Header: x-goog-api-key: $GEMINI_API_KEY
Header: Content-Type: application/json

{
  "instances": [{
    "prompt": "...",
    "image": { "inlineData": { "mimeType": "image/png", "data": "<base64>" } }
  }],
  "parameters": {
    "aspectRatio": "16:9",
    "resolution": "720p",
    "negativePrompt": "...",
    "lastFrame": { "inlineData": { "mimeType": "image/png", "data": "<base64>" } },
    "referenceImages": [
      { "image": { "inlineData": { "mimeType": "image/png", "data": "<base64>" } }, "referenceType": "asset" }
    ]
  }
}
```

Response: `{ "name": "operations/..." }`

### Poll Status
```
GET /v1beta/{operation_name}
Header: x-goog-api-key: $GEMINI_API_KEY
```

Response when done: `{ "done": true, "response": { "generateVideoResponse": { "generatedSamples": [{ "video": { "uri": "..." } }] } } }`

### Download
```
GET {video_uri}
Header: x-goog-api-key: $GEMINI_API_KEY
```

## Constraints

| Constraint | Value |
|-----------|-------|
| Min latency | 11 seconds |
| Max latency (peak) | ~6 minutes |
| Video retention | 2 days |
| Max standard duration | 8 seconds |
| Extension per request | 7 seconds added |
| Max extensions | 20 (148s total) |
| Max input video for extension | 141 seconds |
| Extension resolution | 720p only |
| Extension aspect ratio | 9:16 or 16:9 only |
| Max reference images | 3 |
| Audio | Native (Veo 3.1 and 3); silent on Veo 2 |
| Watermarking | SynthID embedded in all generated videos |
