<?php
$conn = new mysqli("localhost", "root", "", "attendance_system");

if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

$name        = $_POST['student_name'] ?? '';
$student_id  = $_POST['student_id'] ?? '';
$fingerprint = $_POST['fingerprint'] ?? '';
$image       = $_POST['image'] ?? '';

$sql = "INSERT INTO students (student_name, student_id, fingerprint_id, face_encoding) VALUES (?, ?, ?, ?)";

$stmt = $conn->prepare($sql);
$stmt->bind_param("ssss", $name, $student_id, $fingerprint, $image);

if ($stmt->execute()) {
    echo "Student Registered Successfully";
} else {
    echo "Error: " . $stmt->error;
}

$stmt->close();
$conn->close();
?>