using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace Frontend.Controls
{
    /// <summary>
    /// Controls for connection and model selection.
    /// </summary>
    public partial class ConnectionControls : UserControl
    {
        private bool _isConnected;

        /// <summary>
        /// Event fired when connect/disconnect is clicked.
        /// </summary>
        public event Action<bool>? ConnectionToggled;

        public ConnectionControls()
        {
            InitializeComponent();
        }

        /// <summary>
        /// Gets the currently selected model identifier.
        /// </summary>
        public string GetSelectedModel()
        {
            var selectedItem = ModelSelector.SelectedItem as ComboBoxItem;
            return selectedItem?.Tag?.ToString() ?? "gemini-2.5-flash";
        }

        /// <summary>
        /// Sets the connection state and updates the UI.
        /// </summary>
        public void SetConnected(bool isConnected)
        {
            _isConnected = isConnected;

            if (isConnected)
            {
                ConnectButton.Content = "Disconnect";
                ConnectButton.Background = new SolidColorBrush(Color.FromRgb(51, 51, 51));
            }
            else
            {
                ConnectButton.Content = "Connect";
                ConnectButton.Background = new SolidColorBrush(Color.FromRgb(255, 107, 53));
            }
        }

        private void ConnectButton_Click(object sender, RoutedEventArgs e)
        {
            ConnectionToggled?.Invoke(!_isConnected);
        }
    }
}









