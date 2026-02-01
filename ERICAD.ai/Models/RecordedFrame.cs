using System;

namespace Frontend.Models
{
    /// <summary>
    /// Represents a captured screen frame in the recording buffer.
    /// </summary>
    public class RecordedFrame
    {
        /// <summary>
        /// The image data as JPEG bytes.
        /// </summary>
        public byte[] ImageData { get; set; } = Array.Empty<byte>();
        
        /// <summary>
        /// When this frame was captured.
        /// </summary>
        public DateTime Timestamp { get; set; }
        
        /// <summary>
        /// Whether user annotations were visible when this frame was captured.
        /// </summary>
        public bool HasAnnotations { get; set; }
    }
}









