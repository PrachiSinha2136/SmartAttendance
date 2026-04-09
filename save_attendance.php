<?php
$conn = new mysqli("localhost", "root", "", "attendance_system");

$data = json_decode(file_get_contents("php://input"), true);

$student_id = $data['student_id'];
$status = $data['status'];

$attendance_date = date("Y-m-d");
$attendance_time = date("H:i:s");

$sql = "INSERT INTO attendance 
(student_id, attendance_date, attendance_time, status) 
VALUES 
('$student_id', '$attendance_date', '$attendance_time', '$status')";

if ($conn->query($sql) === TRUE) {
    echo json_encode([
        "success" => true
    ]);
} else {
    echo json_encode([
        "success" => false,
        "error" => $conn->error
    ]);
}
?>