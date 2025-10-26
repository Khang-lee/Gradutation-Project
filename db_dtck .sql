-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Máy chủ: 127.0.0.1
-- Thời gian đã tạo: Th10 26, 2025 lúc 12:38 PM
-- Phiên bản máy phục vụ: 10.4.32-MariaDB
-- Phiên bản PHP: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Cơ sở dữ liệu: `db_dtck`
--

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `classification_history`
--

CREATE TABLE `classification_history` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `label_name` varchar(255) NOT NULL COMMENT 'Tên nhãn dự đoán (dạng chữ)',
  `confidence` float DEFAULT NULL,
  `file_path` varchar(255) DEFAULT NULL,
  `uploaded_at` timestamp NOT NULL DEFAULT current_timestamp() COMMENT 'Thời gian phân loại/upload'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `labels`
--

CREATE TABLE `labels` (
  `id` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `handling_suggestion` text DEFAULT NULL COMMENT 'Gợi ý cách xử lý loại rác này',
  `created_by_admin_id` int(11) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `labels`
--

INSERT INTO `labels` (`id`, `name`, `description`, `handling_suggestion`, `created_by_admin_id`, `created_at`) VALUES
(1, 'paper', 'Các loại giấy, báo, tạp chí.', 'Để khô ráo, không lẫn thức ăn, bỏ vào thùng rác tái chế màu xanh dương hoặc nơi thu gom giấy vụn.', 1, '2025-10-18 11:02:07'),
(2, 'metal', 'Các loại vỏ lon, kim loại.', 'Bỏ vào thùng rác tái chế màu xám hoặc nơi thu gom kim loại.', 1, '2025-10-18 11:02:07'),
(3, 'plastic', 'Chai nhựa, túi nilon, hộp nhựa.', 'Làm sạch, làm khô, bỏ vào thùng rác tái chế màu vàng hoặc nơi thu gom nhựa.', 1, '2025-10-18 11:02:07'),
(4, 'organic', 'Rác hữu cơ, thức ăn thừa, rau củ quả.', 'Thu gom riêng để ủ phân compost tại nhà hoặc bỏ vào thùng rác hữu cơ màu xanh lá cây.', 1, '2025-10-18 11:02:07'),
(5, 'other', 'Các loại rác khác không thuộc các nhóm trên.', 'Đây là rác thải thông thường không thể tái chế hoặc phân hủy sinh học. Bỏ vào thùng rác thông thường màu xám.', 1, '2025-10-18 11:02:07'),
(6, 'cardboard', 'Bìa carton, hộp giấy cứng.', 'Làm phẳng, để khô ráo, bỏ vào thùng rác tái chế màu xanh dương hoặc nơi thu gom giấy vụn.', 1, '2025-10-18 11:02:07');

-- --------------------------------------------------------

--
-- Cấu trúc bảng cho bảng `users`
--

CREATE TABLE `users` (
  `id` int(100) NOT NULL,
  `username` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin','user') NOT NULL DEFAULT 'user',
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Đang đổ dữ liệu cho bảng `users`
--

INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`) VALUES
(1, '1', '1', 'user', '2025-10-18 09:25:28');

--
-- Chỉ mục cho các bảng đã đổ
--

--
-- Chỉ mục cho bảng `classification_history`
--
ALTER TABLE `classification_history`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Chỉ mục cho bảng `labels`
--
ALTER TABLE `labels`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `name` (`name`),
  ADD KEY `created_by_admin_id` (`created_by_admin_id`);

--
-- Chỉ mục cho bảng `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT cho các bảng đã đổ
--

--
-- AUTO_INCREMENT cho bảng `classification_history`
--
ALTER TABLE `classification_history`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT cho bảng `labels`
--
ALTER TABLE `labels`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT cho bảng `users`
--
ALTER TABLE `users`
  MODIFY `id` int(100) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=33;

--
-- Các ràng buộc cho các bảng đã đổ
--

--
-- Các ràng buộc cho bảng `classification_history`
--
ALTER TABLE `classification_history`
  ADD CONSTRAINT `classification_history_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`);

--
-- Các ràng buộc cho bảng `labels`
--
ALTER TABLE `labels`
  ADD CONSTRAINT `labels_ibfk_1` FOREIGN KEY (`created_by_admin_id`) REFERENCES `users` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
