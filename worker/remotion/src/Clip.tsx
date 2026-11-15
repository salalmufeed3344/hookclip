import React from "react";
import {
	AbsoluteFill,
	Video,
	interpolate,
	spring,
	staticFile,
	useCurrentFrame,
	useVideoConfig,
} from "remotion";

export type CaptionWord = { w: string; s: number; e: number };

export type ClipProps = {
	/** File staged in public/, e.g. "input-abc123.mp4". */
	video: string;
	/** Word timings in seconds, relative to the clip start. */
	words: CaptionWord[];
	hook: string;
	watermark: boolean;
	durationSec: number;
};

const FONT = "DejaVu Sans, sans-serif";

/** Same grouping as render.py's ASS captions: ~5 words / <= 2.5s per line. */
function groupWords(words: CaptionWord[]) {
	const groups: { words: CaptionWord[]; start: number; end: number }[] = [];
	let cur: CaptionWord[] = [];
	let start = 0;
	for (const w of words) {
		if (cur.length === 0) {
			start = w.s;
		}
		cur.push(w);
		if (cur.length >= 5 || w.e - start >= 2.5) {
			groups.push({ words: cur, start, end: w.e });
			cur = [];
		}
	}
	if (cur.length > 0) {
		groups.push({ words: cur, start, end: cur[cur.length - 1].e });
	}
	return groups;
}

export const Clip: React.FC<ClipProps> = ({ video, words, hook, watermark }) => {
	const frame = useCurrentFrame();
	const { fps } = useVideoConfig();
	const t = frame / fps;

	const groups = groupWords(words);
	const active = groups.find((g) => t >= g.start - 0.05 && t <= g.end + 0.25);

	const hookScale = spring({ frame, fps, config: { damping: 100 } });
	const hookOpacity = interpolate(frame, [0, 8], [0, 1]);
	const showHook = t < 3 && hook.trim().length > 0;

	return (
		<AbsoluteFill style={{ backgroundColor: "black" }}>
			<AbsoluteFill>
				<Video src={staticFile(video)} />
			</AbsoluteFill>

			{showHook ? (
				<div
					style={{
						position: "absolute",
						top: 260,
						left: 60,
						right: 60,
						textAlign: "center",
						fontFamily: FONT,
						fontSize: 76,
						fontWeight: 800,
						color: "#FFB800",
						lineHeight: 1.15,
						textShadow: "0 4px 0 rgba(0,0,0,0.6)",
						opacity: hookOpacity,
						transform: `scale(${interpolate(hookScale, [0, 1], [0.92, 1])})`,
					}}
				>
					{hook}
				</div>
			) : null}

			{active ? (
				<div
					style={{
						position: "absolute",
						bottom: 150,
						left: 40,
						right: 40,
						textAlign: "center",
						fontFamily: FONT,
						fontSize: 64,
						fontWeight: 800,
						lineHeight: 1.25,
						textShadow:
							"0 3px 0 rgba(0,0,0,0.8), 0 0 24px rgba(0,0,0,0.8)",
					}}
				>
					{active.words.map((w, i) => {
						const isCurrent = t >= w.s && t < w.e;
						return (
							<span
								key={i}
								style={{
									color: isCurrent ? "#FFB800" : "#FFFFFF",
									display: "inline-block",
									transform: isCurrent ? "scale(1.12)" : "scale(1)",
									// Space between words as a margin, not a text
									// node: whitespace inside an inline-block
									// span collapses, so words ran together
									// ("Watchthisplay") without it.
									marginRight: "0.28em",
								}}
							>
								{w.w}
							</span>
						);
					})}
				</div>
			) : null}

			{watermark ? (
				<div
					style={{
						position: "absolute",
						right: 28,
						bottom: 28,
						fontFamily: FONT,
						fontSize: 30,
						color: "rgba(255,255,255,0.7)",
						textShadow: "0 1px 0 rgba(0,0,0,0.5)",
					}}
				>
					Hookclip
				</div>
			) : null}
		</AbsoluteFill>
	);
};
