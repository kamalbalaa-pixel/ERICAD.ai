using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace Frontend.Controls
{
    /// <summary>
    /// Controls for screen capture and recording status.
    /// </summary>
    public partial class CaptureControls : UserControl
    {
        /// <summary>
        /// Event fired when capture is requested.
        /// </summary>
        public event Action<int>? CaptureRequested;

        /// <summary>
        /// Event fired when new chat is requested.
        /// </summary>
        public event Action? NewChatRequested;

        public CaptureControls()
        {
            InitializeComponent();
        }

        /// <summary>
        /// Enables or disables the controls.
        /// </summary>
        public void SetEnabled(bool enabled)
        {
            TimeSelector.IsEnabled = enabled;
            CaptureButton.IsEnabled = enabled;
            NewChatButton.IsEnabled = enabled;
        }

        /// <summary>
        /// Sets the capture button enabled state.
        /// </summary>
        public void SetCaptureEnabled(bool enabled)
        {
            CaptureButton.IsEnabled = enabled;
        }

        /// <summary>
        /// Shows or hides the recording status indicator.
        /// </summary>
        public void SetRecordingVisible(bool visible)
        {
            RecordingStatusBorder.Visibility = visible ? Visibility.Visible : Visibility.Collapsed;
        }

        /// <summary>
        /// Updates the recording status display.
        /// </summary>
        public void UpdateRecordingStatus(TimeSpan duration)
        {
            var minutes = (int)duration.TotalMinutes;
            var seconds = (int)(duration.TotalSeconds % 60);
            RecordingStatusText.Text = $"Recording: {minutes}:{seconds:D2} / 7:30";

            // Animate recording dot
            RecordingDot.Fill = RecordingDot.Fill == Brushes.Red
                ? new SolidColorBrush(Color.FromRgb(100, 30, 30))
                : Brushes.Red;
        }

        /// <summary>
        /// Updates the image status display.
        /// </summary>
        public void SetImageStatus(bool hasImage, string statusText)
        {
            if (hasImage)
            {
                ImageStatusBorder.Visibility = Visibility.Visible;
                ImageStatusText.Text = statusText;
                ImageStatusText.Foreground = new SolidColorBrush(Color.FromRgb(100, 200, 100));
            }
            else
            {
                ImageStatusBorder.Visibility = Visibility.Collapsed;
            }
        }

        /// <summary>
        /// Gets the selected time in seconds.
        /// </summary>
        public int GetSelectedSeconds()
        {
            var selectedItem = TimeSelector.SelectedItem as ComboBoxItem;
            return int.Parse(selectedItem?.Tag?.ToString() ?? "0");
        }

        private void CaptureButton_Click(object sender, RoutedEventArgs e)
        {
            var seconds = GetSelectedSeconds();
            CaptureRequested?.Invoke(seconds);
        }

        private void NewChatButton_Click(object sender, RoutedEventArgs e)
        {
            NewChatRequested?.Invoke();
        }
    }
}









