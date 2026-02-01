using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Frontend.Models;

namespace Frontend.Services
{
    /// <summary>
    /// Handles screenshot capture and frame processing for sending to the AI.
    /// </summary>
    public class ScreenCaptureService
    {
        /// <summary>
        /// Action to temporarily hide UI during capture.
        /// </summary>
        public Action? OnBeforeCapture { get; set; }

        /// <summary>
        /// Action to restore UI after capture.
        /// </summary>
        public Action? OnAfterCapture { get; set; }

        /// <summary>
        /// Maximum number of frames to send to the AI.
        /// </summary>
        public int MaxFramesToSend { get; set; } = 30;

        /// <summary>
        /// JPEG quality for screenshots (0-100).
        /// </summary>
        public long JpegQuality { get; set; } = 85;

        /// <summary>
        /// Captures a screenshot and returns it as base64.
        /// </summary>
        public async Task<string> CaptureScreenshotAsync()
        {
            return await Task.Run(() =>
            {
                OnBeforeCapture?.Invoke();

                try
                {
                    using var bitmap = new Bitmap(1920, 1080, PixelFormat.Format32bppArgb);
                    using (var graphics = Graphics.FromImage(bitmap))
                    {
                        graphics.CopyFromScreen(0, 0, 0, 0, new Size(1920, 1080), CopyPixelOperation.SourceCopy);
                    }

                    using var memoryStream = new MemoryStream();
                    var encoder = GetEncoder(ImageFormat.Jpeg);
                    var encoderParams = new EncoderParameters(1);
                    encoderParams.Param[0] = new EncoderParameter(Encoder.Quality, JpegQuality);
                    bitmap.Save(memoryStream, encoder, encoderParams);

                    return Convert.ToBase64String(memoryStream.ToArray());
                }
                finally
                {
                    OnAfterCapture?.Invoke();
                }
            });
        }

        /// <summary>
        /// Prepares recorded frames for sending to the AI.
        /// </summary>
        public FramesPayload PrepareFramesPayload(List<RecordedFrame> frames, int requestedSeconds)
        {
            if (frames.Count == 0)
            {
                return new FramesPayload { IsEmpty = true };
            }

            // Calculate actual duration
            var actualDuration = frames.Count > 1
                ? (frames.Last().Timestamp - frames.First().Timestamp).TotalSeconds
                : 0;

            // Sample frames evenly to limit payload size
            var sampledFrames = SampleFrames(frames, MaxFramesToSend);

            // Check for any annotations in the frames
            var hasAnyAnnotations = sampledFrames.Any(f => f.HasAnnotations);

            // Convert frames to transfer format
            var framesData = sampledFrames.Select(f => new FrameData
            {
                Data = Convert.ToBase64String(f.ImageData),
                Timestamp = f.Timestamp.ToString("o"),
                HasAnnotations = f.HasAnnotations
            }).ToList();

            return new FramesPayload
            {
                Type = "frames",
                Frames = framesData,
                Duration = requestedSeconds,
                ActualDuration = actualDuration,
                FrameCount = sampledFrames.Count,
                HasAnnotations = hasAnyAnnotations,
                IsEmpty = false
            };
        }

        private List<RecordedFrame> SampleFrames(List<RecordedFrame> frames, int maxFrames)
        {
            if (frames.Count <= maxFrames)
            {
                return frames;
            }

            var step = (double)frames.Count / maxFrames;
            var sampled = new List<RecordedFrame>();

            for (int i = 0; i < maxFrames; i++)
            {
                var index = (int)(i * step);
                if (index < frames.Count)
                {
                    sampled.Add(frames[index]);
                }
            }

            return sampled;
        }

        private static ImageCodecInfo GetEncoder(ImageFormat format)
        {
            var codecs = ImageCodecInfo.GetImageEncoders();
            return codecs.First(c => c.FormatID == format.Guid);
        }
    }

    /// <summary>
    /// Data for a single frame to be sent to the AI.
    /// </summary>
    public class FrameData
    {
        public string Data { get; set; } = "";
        public string Timestamp { get; set; } = "";
        public bool HasAnnotations { get; set; }
    }

    /// <summary>
    /// Payload containing multiple frames to send to the AI.
    /// </summary>
    public class FramesPayload
    {
        public string Type { get; set; } = "frames";
        public List<FrameData> Frames { get; set; } = new();
        public int Duration { get; set; }
        public double ActualDuration { get; set; }
        public int FrameCount { get; set; }
        public bool HasAnnotations { get; set; }
        public bool IsEmpty { get; set; }
    }
}









