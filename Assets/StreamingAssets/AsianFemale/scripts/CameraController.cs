using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CameraController : MonoBehaviour
{
    public float speed = 5f;          // Movement speed
    public float jumpForce = 5f;     // Force applied for jumping
    public float minHeight = 1f;     // Minimum height to stay above the plane
    public float mouseSensitivity = 2f; // Sensitivity for mouse movement
    private Rigidbody rb;            // Rigidbody for physics-based movement
    private bool isGrounded = true;  // Check if the camera is on the ground

    private float rotationX = 0f;    // Vertical rotation
    private float rotationY = 0f;    // Horizontal rotation

    void Start()
    {
        // Get the Rigidbody component attached to the camera
        rb = GetComponent<Rigidbody>();
        if (rb == null)
        {
            // Add a Rigidbody if not already attached
            rb = gameObject.AddComponent<Rigidbody>();
            rb.freezeRotation = true; // Prevent the Rigidbody from rotating
        }
    }

    void Update()
    {
        // Get movement inputs (WASD or Arrow keys)
        float horizontal = Input.GetAxis("Horizontal"); // A/D or Left/Right
        float vertical = Input.GetAxis("Vertical");     // W/S or Up/Down

        // Prevent falling below the minimum height
        if (transform.position.y < minHeight)
        {
            transform.position = new Vector3(transform.position.x, minHeight, transform.position.z);
        }

        // Move the camera
        Vector3 move = new Vector3(horizontal, 0, vertical);
        transform.Translate(move * speed * Time.deltaTime, Space.Self);

        // Check for jump input
        if (Input.GetKeyDown(KeyCode.Space) && isGrounded)
        {
            rb.AddForce(Vector3.up * jumpForce, ForceMode.Impulse);
            isGrounded = false; // Set grounded to false after jumping
        }

        // Rotate the camera view with the mouse when left button is held
        if (Input.GetMouseButton(0)) // Left mouse button
        {
            float mouseX = Input.GetAxis("Mouse X") * mouseSensitivity;
            float mouseY = Input.GetAxis("Mouse Y") * mouseSensitivity;

            // Adjust the rotation based on mouse movement
            rotationX -= mouseY;
            rotationY += mouseX;

            // Clamp vertical rotation to avoid flipping
            rotationX = Mathf.Clamp(rotationX, -90f, 90f);

            // Apply the rotation to the camera
            transform.localRotation = Quaternion.Euler(rotationX, rotationY, 0f);
        }
    }

    private void OnCollisionEnter(Collision collision)
    {
        // Check if the camera collides with the ground
        if (collision.gameObject.CompareTag("Ground"))
        {
            isGrounded = true;
        }
    }
}


