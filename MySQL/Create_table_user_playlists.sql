CREATE TABLE IF NOT EXISTS user_playlists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    playlist_name VARCHAR(100) NOT NULL,
    streamers VARCHAR(255) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES twitch_users(id) ON DELETE CASCADE
);