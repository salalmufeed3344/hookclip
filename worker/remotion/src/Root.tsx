import React from "react";
import { Composition } from "remotion";
import { Clip, ClipProps } from "./Clip";

/**
 * One composition: a 1080x1920 clip with animated word-by-word captions
 * and a hook overlay, rendered over the ffmpeg-reframed video that the
 * Python worker stages into public/ as input-<id>.mp4.
 *
 * durationInFrames comes from props.durationSec via calculateMetadata so
 * the worker can render any clip length (15–60s).
 */
export const RemotionRoot: React.FC = () => {
	return (
		<Composition
			id="HookclipCaption"
			component={Clip}
			durationInFrames={1350}
			fps={30}
			width={1080}
			height={1920}
			defaultProps={
				{
					video: "input.mp4",
					words: [],
					hook: "",
					watermark: true,
					durationSec: 45,
				} as ClipProps
			}
			calculateMetadata={async ({ props }) => {
				const durationSec = (props as ClipProps).durationSec || 45;
				return { durationInFrames: Math.max(30, Math.round(durationSec * 30)) };
			}}
		/>
	);
};
