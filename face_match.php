<!-- face_match.php -->

<?php
header('Content-Type: application/json');

$conn = new mysqli("localhost", "root", "", "attendance_system");

if ($conn->connect_error) {
    echo json_encode([
        "success" => false,
        "message" => "Database connection failed"
    ]);
    exit;
}

$data = json_decode(file_get_contents("php://input"), true);

$student_id = $data['student_id'] ?? '';

if ($student_id == '') {
    echo json_encode([
        "success" => false,
        "message" => "Student ID missing"
    ]);
    exit;
}

$sql = "SELECT face_encoding, name FROM students WHERE id='$student_id'";
$result = $conn->query($sql);

if ($result->num_rows > 0) {
    $student = $result->fetch_assoc();

    // Dummy face match
    $faceMatched = true;

    if ($faceMatched) {
        echo json_encode([
            "success" => true,
            "student_name" => $student['name'],
            "message" => "Face matched successfully"
        ]);
    } else {
        echo json_encode([
            "success" => false,
            "message" => "Face not matched"
        ]);
    }
} else {
    echo json_encode([
        "success" => false,
        "message" => "Student not found"
    ]);
}

$conn->close();
?>