CREATE TABLE IF NOT EXISTS streamer_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    streamer_name VARCHAR(100) NOT NULL,
    preference ENUM('like', 'dislike') NOT NULL,
    UNIQUE KEY unique_user_streamer (user_id, streamer_name),
    FOREIGN KEY (user_id) REFERENCES twitch_users(id) ON DELETE CASCADE
);