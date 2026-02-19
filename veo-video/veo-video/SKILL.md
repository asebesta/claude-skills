---
name: veo-video
description: >
  Generate videos using Google's Veo 3.1 API via the @google/genai SDK (JavaScript/TypeScript).
  Use when the user wants to: generate video from a text prompt, animate an image into video,
  interpolate between two frames, extend an existing video, use reference images for style/asset
  guidance, or build any application involving AI video generation with Veo.
  Triggers on mentions of: Veo, video generation, text-to-video, image-to-video, AI video.
---

# Veo 3.1 Video Generation

Model: `veo-3.1-generate-preview`
SDK: `@google/genai` (npm)
Auth: `GEMINI_API_KEY` environment variable (or pass `apiKey` to `GoogleGenAI` constructor)

## Core Pattern

Every Veo workflow follows: **generate -> poll -> download**.

```javascript
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({});

// 1. Start generation
let operation = await ai.models.generateVideos({
  model: "veo-3.1-generate-preview",
  prompt: "A cinematic shot of a majestic lion in the savannah",
  config: {
    aspectRatio: "16:9",       // "16:9" (default) | "9:16"
    resolution: "720p",        // "720p" (default) | "1080p" | "4k"
    negativePrompt: "cartoon, low quality",
  },
});

// 2. Poll until done (10s intervals)
while (!operation.done) {
  await new Promise((r) => setTimeout(r, 10_000));
  operation = await ai.operations.getVideosOperation({ operation });
}

// 3. Download
ai.files.download({
  file: operation.response.generatedVideos[0].video,
  downloadPath: "output.mp4",
});
```

## Prompting

Structure prompts as: **[Shot Type] + [Subject] + [Action] + [Setting] + [Lighting] + [Style] + [Technical]**

```
"Slow motion close-up of coffee being poured into a white ceramic cup,
steam rising, morning sunlight streaming through window, warm color grading,
cinematic, 4K, shallow depth of field"
```

For audio: use quotation marks for dialogue (`A man says, "Look at that."`), and describe sound effects/ambience explicitly.

For the full vocabulary of shot types, camera movements, lighting, style keywords, and audio prompting tips, see [references/prompting.md](references/prompting.md).

## Generation Modes

### Text-to-Video
Pass `prompt` only. Audio is generated natively — use quotation marks for dialogue, describe sound effects and ambience in the prompt.

### Image-to-Video
Pass `prompt` + `image` to animate a starting frame:
```javascript
await ai.models.generateVideos({
  model: "veo-3.1-generate-preview",
  prompt: "Panning wide shot of a calico kitten sleeping in sunshine",
  image: {
    imageBytes: base64ImageData,  // or from a Gemini image generation
    mimeType: "image/png",
  },
});
```

### Frame Interpolation
Pass `prompt` + `image` (first frame) + `config.lastFrame` (last frame):
```javascript
await ai.models.generateVideos({
  model: "veo-3.1-generate-preview",
  prompt: "Ghostly woman fading from a rope swing in moonlit clearing",
  image: firstFrameImage,
  config: { lastFrame: lastFrameImage },
});
```

### Reference Images (max 3)
Guide style/assets with `config.referenceImages`. Each entry needs `referenceType: "asset"`:
```javascript
await ai.models.generateVideos({
  model: "veo-3.1-generate-preview",
  prompt: "Woman wearing flamingo dress walks through a lagoon",
  config: {
    referenceImages: [
      { image: dressImage, referenceType: "asset" },
      { image: glassesImage, referenceType: "asset" },
    ],
  },
});
```

### Video Extension
Pass `video` (previous Veo output) + `prompt`. Limited to 720p, 7s per extension, up to 20 extensions (148s total). Input video max 141s.
```javascript
await ai.models.generateVideos({
  model: "veo-3.1-generate-preview",
  video: previousOperationVideo,
  prompt: "Butterfly lands on an orange origami flower",
  config: { numberOfVideos: 1, resolution: "720p" },
});
```

## Config Reference

For the full parameter table, REST API details, and constraints, see [references/api.md](references/api.md).

Key constraints:
- **Duration**: `"4"`, `"6"`, or `"8"` seconds. `"8"` required for 1080p/4k/extension/references.
- **Resolution**: 1080p and 4k only available at 8s duration.
- **Latency**: 11s minimum, up to 6 minutes at peak.
- **Retention**: Generated videos stored for 2 days — download promptly.
- **Audio**: Natively generated with video. Use prompt cues for dialogue/SFX.
- **Safety**: All videos watermarked with SynthID. Content may be filtered by safety policies.
