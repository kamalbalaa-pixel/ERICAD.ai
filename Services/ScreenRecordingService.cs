using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Linq;
using System.Windows.Threading;
using Frontend.Models;

namespace Frontend.Services
{
    /// <summary>
    /// Manages continuous screen recording with a rolling buffer.
    /// </summary>
    public class ScreenRecordingService
    {
        private readonly List<RecordedFrame> _frameBuffer = new();
        private readonly object _bufferLock = new();
        private DispatcherTimer? _recordingTimer;
        private DispatcherTimer? _statusUpdateTimer;
        private DateTime _recordingStartTime;

        // Recording configuration
        // First 2:30 (150s) at 5 FPS = 750 frames
        // Next 5:00 (300s) at 0.5 FPS = 150 frames
        // Total: 7:30 (450s), ~900 frames max
        private const int HIGH_QUALITY_DURATION_SECONDS = 150; // 2:30
        private const double HIGH_QUALITY_FPS = 5.0;
        private const double LOW_QUALITY_FPS = 0.5;
        private const int MAX_BUFFER_SECONDS = 450; // 7:30

        /// <summary>
        /// Whether recording is currently active.
        /// </summary>
        public bool IsRecording { get; private set; }

        /// <summary>
        /// Function to check if user has annotations visible.
        /// </summary>
        public Func<bool>? HasAnnotationsCheck { get; set; }

        /// <summary>
        /// Action to temporarily hide UI during capture.
        /// </summary>
        public Action? OnBeforeCapture { get; set; }

        /// <summary>
        /// Action to restore UI after capture.
        /// </summary>
        public Action? OnAfterCapture { get; set; }

        /// <summary>
        /// Event fired when recording status should be updated.
        /// </summary>
        public event Action<TimeSpan>? StatusUpdated;

        public void Start()
        {
            if (IsRecording) return;

            IsRecording = true;
            _recordingStartTime = DateTime.Now;

            lock (_bufferLock)
            {
                _frameBuffer.Clear();
            }

            // Start the recording timer - capture at high FPS initially
            _recordingTimer = new DispatcherTimer
            {
                Interval = TimeSpan.FromMilliseconds(1000.0 / HIGH_QUALITY_FPS)
            };
            _recordingTimer.Tick += RecordingTimer_Tick;
            _recordingTimer.Start();

            // Start status update timer
            _statusUpdateTimer = new DispatcherTimer
            {
                Interval = TimeSpan.FromMilliseconds(500)
            };
            _statusUpdateTimer.Tick += StatusUpdateTimer_Tick;
            _statusUpdateTimer.Start();
        }

        public void Stop()
        {
            IsRecording = false;

            _recordingTimer?.Stop();
            _recordingTimer = null;

            _statusUpdateTimer?.Stop();
            _statusUpdateTimer = null;
        }

        public void Reset()
        {
            lock (_bufferLock)
            {
                _frameBuffer.Clear();
            }
            _recordingStartTime = DateTime.Now;
        }

        private void RecordingTimer_Tick(object? sender, EventArgs e)
        {
            if (!IsRecording) return;

            // Determine current frame rate based on buffer age
            var bufferDuration = GetBufferDuration();

            // Adjust timer interval based on how old our oldest frame is
            if (bufferDuration.TotalSeconds >= HIGH_QUALITY_DURATION_SECONDS)
            {
                // Switch to low quality FPS for frames older than 2:30
                if (_recordingTimer != null && _recordingTimer.Interval.TotalMilliseconds < 1500)
                {
                    _recordingTimer.Interval = TimeSpan.FromMilliseconds(1000.0 / LOW_QUALITY_FPS);
                }
            }

            CaptureFrameToBuffer();
            PruneOldFrames();
        }

        private void StatusUpdateTimer_Tick(object? sender, EventArgs e)
        {
            StatusUpdated?.Invoke(GetBufferDuration());
        }

        public TimeSpan GetBufferDuration()
        {
            lock (_bufferLock)
            {
                if (_frameBuffer.Count < 2) return TimeSpan.Zero;

                var oldest = _frameBuffer.Min(f => f.Timestamp);
                var newest = _frameBuffer.Max(f => f.Timestamp);
                return newest - oldest;
            }
        }

        private void CaptureFrameToBuffer()
        {
            try
            {
                OnBeforeCapture?.Invoke();

                byte[] imageData;
                using (var bitmap = new Bitmap(1920, 1080, PixelFormat.Format32bppArgb))
                {
                    using (var graphics = Graphics.FromImage(bitmap))
                    {
                        graphics.CopyFromScreen(0, 0, 0, 0, new Size(1920, 1080), CopyPixelOperation.SourceCopy);
                    }

                    using (var memoryStream = new MemoryStream())
                    {
                        // Use lower quality JPEG for buffer efficiency
                        var encoder = GetEncoder(ImageFormat.Jpeg);
                        var encoderParams = new EncoderParameters(1);
                        encoderParams.Param[0] = new EncoderParameter(Encoder.Quality, 60L);
                        bitmap.Save(memoryStream, encoder, encoderParams);
                        imageData = memoryStream.ToArray();
                    }
                }

                OnAfterCapture?.Invoke();

                // Add frame to buffer
                lock (_bufferLock)
                {
                    _frameBuffer.Add(new RecordedFrame
                    {
                        ImageData = imageData,
                        Timestamp = DateTime.Now,
                        HasAnnotations = HasAnnotationsCheck?.Invoke() ?? false
                    });
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Frame capture error: {ex.Message}");
                OnAfterCapture?.Invoke();
            }
        }

        private static ImageCodecInfo GetEncoder(ImageFormat format)
        {
            var codecs = ImageCodecInfo.GetImageEncoders();
            return codecs.First(c => c.FormatID == format.Guid);
        }

        private void PruneOldFrames()
        {
            lock (_bufferLock)
            {
                var cutoffTime = DateTime.Now.AddSeconds(-MAX_BUFFER_SECONDS);
                _frameBuffer.RemoveAll(f => f.Timestamp < cutoffTime);

                // Also thin out old frames to maintain the FPS structure
                // Keep high-quality (5 FPS) for recent 2:30
                // Keep low-quality (0.5 FPS) for older 5:00
                var recentCutoff = DateTime.Now.AddSeconds(-HIGH_QUALITY_DURATION_SECONDS);

                var oldFrames = _frameBuffer.Where(f => f.Timestamp < recentCutoff).OrderBy(f => f.Timestamp).ToList();
                if (oldFrames.Count > 10)
                {
                    // Keep only every 10th frame for old section (0.5 FPS from 5 FPS = keep 1 in 10)
                    var framesToRemove = new List<RecordedFrame>();
                    for (int i = 0; i < oldFrames.Count; i++)
                    {
                        if (i % 10 != 0)
                        {
                            framesToRemove.Add(oldFrames[i]);
                        }
                    }
                    foreach (var frame in framesToRemove)
                    {
                        _frameBuffer.Remove(frame);
                    }
                }
            }
        }

        /// <summary>
        /// Gets frames for the specified duration.
        /// </summary>
        public List<RecordedFrame> GetFramesForDuration(int seconds)
        {
            lock (_bufferLock)
            {
                var cutoffTime = DateTime.Now.AddSeconds(-seconds);
                return _frameBuffer.Where(f => f.Timestamp >= cutoffTime)
                                   .OrderBy(f => f.Timestamp)
                                   .ToList();
            }
        }

        /// <summary>
        /// Formats a duration in seconds as a readable string.
        /// </summary>
        public static string FormatDuration(int seconds)
        {
            var minutes = seconds / 60;
            var secs = seconds % 60;
            return minutes > 0 ? $"{minutes}:{secs:D2}" : $"{secs}s";
        }
    }
}









