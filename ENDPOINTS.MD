## General

### `GET /`
*   **Description**: Basic health check endpoint to test if the application is available.
*   **Request**: None
*   **Response**:
    *   **Success (200 OK)**:
        ```json
        {"message": "Hello, World!"}
        ```

### `GET /favicon.ico`
*   **Description**: Returns the favicon icon image for the application.
*   **Request**: None
*   **Response**:
    *   **Success (200 OK)**: The `favicon.ico` file.

## Fake News (prefix: `/api/v2`)
Endpoints for detecting fake news. These endpoints are rate-limited as described in rate_limits.md.

### `GET /api/v2/fake_news_check/{prompt}`
*   **Description**: Analyzes the provided text (via path parameter) to check if it's fake news.
*   **Request**:
    *   **Path Parameters**:
        *   `prompt` (string): The news text or claim to verify.
*   **Response**:
    *   **Success (200 OK)**:
        ```json
        {
          "result": "analysis_details", // Detailed analysis
          "is_fake": true,              // boolean
          "confidence": 0.85            // float (0.0 to 1.0)
        }
        ```
    *   **Error (429 Too Many Requests)**: If rate limit is exceeded. See rate_limits.md.

### `GET /api/v2/fake_news_check`
*   **Description**: Analyzes the provided text (via query parameter) to check if it's fake news.
*   **Request**:
    *   **Query Parameters**:
        *   `prompt` (string): The news text or claim to verify.
*   **Response**:
    *   **Success (200 OK)**:
        ```json
        {
          "result": "analysis_details", // Detailed analysis
          "is_fake": false,             // boolean
          "confidence": 0.95            // float (0.0 to 1.0)
        }
        ```
    *   **Error (429 Too Many Requests)**: If rate limit is exceeded. See rate_limits.md.

## User (prefix: `/api`)
Endpoints for user management and authentication.

### `POST /api/register`
*   **Description**: Registers a new user in the system.
*   **Request**:
    *   **Body**: `UserCreateWithKey`
        ```json
        {
          "email": "user@example.com",
          "password": "securepassword123",
          "full_name": "New User",
          "registration_key": "valid-reg-key"
        }
        ```
*   **Response**:
    *   **Success (200 OK)**: `UserOut` (User object without sensitive data)
        ```json
        {
          "id": 1,
          "email": "user@example.com",
          "full_name": "New User",
          "is_active": true,
          "is_admin": false,
          "created_at": "2023-01-01T12:00:00Z"
        }
        ```

### `POST /api/login`
*   **Description**: Authenticates an existing user and returns a JWT access token.
*   **Request**:
    *   **Body**: `UserLogin`
        ```json
        {
          "email": "user@example.com",
          "password": "securepassword123"
        }
        ```
*   **Response**:
    *   **Success (200 OK)**: `TokenResponse`
        ```json
        {
          "access_token": "your_jwt_token_here",
          "token_type": "bearer"
        }
        ```

### `GET /api/me`
*   **Description**: Returns information about the currently authenticated user.
*   **Request**:
    *   **Headers**:
        *   `Authorization: Bearer {token}`
*   **Response**:
    *   **Success (200 OK)**: `UserOut` (User object)

### `POST /api/complete-google-registration`
*   **Description**: Completes the registration process for users who signed up via Google OAuth and need to provide additional details.
*   **Request**:
    *   **Headers**:
        *   `Authorization: Bearer {token}` (Token obtained after Google OAuth callback, if user is new)
    *   **Body**: `CompleteRegistrationRequest`
        ```json
        {
          "email": "user.from.google@example.com", // Should match Google email
          "full_name": "Google User FullName"
        }
        ```
*   **Response**:
    *   **Success (200 OK)**:
        ```json
        {"message": "Registration completed successfully"}
        ```

### `POST /api/check_user_password`
*   **Description**: Checks if the provided password for the user exists.
    *   **Body**: `UserCheckRequest`
        ```json
            {
                "email": "user@example.com",
                "token": "verification_token"
            }
        ```
*   **Response**:
    *   **Success (200 OK)**:
        ```json
        {"message": "Password is exists"}
        ```
    *   **Error (e.g., 400 Bad Request or 401 Unauthorized)**: If password is exists or user not found.

## Admin (prefix: `/api/admin`)
Endpoints for administrative functionalities. Require admin authentication.

### `POST /api/admin/generate-keys`
*   **Description**: Generates a specified number of new registration keys.
*   **Request**:
    *   **Headers**:
        *   `Authorization: Bearer {admin_token}`
    *   **Query Parameters**:
        *   `count` (integer, optional, default: 1): Number of keys to generate (1-100).
*   **Response**:
    *   **Success (200 OK)**:
        ```json
        {
          "keys": ["new_key_1", "new_key_2"] // List of generated key strings
        }
        ```

### `GET /api/admin/list-keys`
*   **Description**: Lists all existing registration keys and their status.
*   **Request**:
    *   **Headers**:
        *   `Authorization: Bearer {admin_token}`
*   **Response**:
    *   **Success (200 OK)**: A list of registration key objects.
        ```json
        [
          {"key_value": "key1_value", "is_used": false, "created_at": "...", "user_id": null},
          {"key_value": "key2_value", "is_used": true, "created_at": "...", "user_id": 5}
        ]
        ```
### `DELETE /api/admin/delete-key`
*   **Description**: Deletes a beta (registration) key by its value or ID. Requires admin authentication.
*   **Request**:
    *   **Headers**:
        *   `Authorization: Bearer {admin_token}`
    *   **Body**: `DeleteKeyRequest`
        ```json
        {
          "id": 123,                  // Optional: Key ID
          "key_value": "key_string"   // Optional: Key value
        }
        ```
        Note: At least one of `id` or `key_value` must be provided.
*   **Response**:
    *   **Success (200 OK)**:
        ```json
        {
          "detail": "Key deleted successfully."
        }
        ```
    *   **Error (404 Not Found)**:
        ```json
        {
          "detail": "Key not found."
        }
        ```
    *   **Error (401 Unauthorized)**: If the user is not an admin or not authenticated.
        ```json
        {
          "detail": "Not authorized."
        }
        ```

### `GET /api/admin/telemetry`
*   **Description**: Retrieves telemetry data.
*   **Request**:
    *   **Headers**:
        *   `Authorization: Bearer {admin_token}`
*   **Response**:
    *   **Success (200 OK)**: Telemetry data (specific JSON structure depends on `get_metrics`).

### `GET /api/admin/rate-limit-stats`
*   **Description**: Retrieves statistics about rate limiting.
*   **Request**:
    *   **Headers**:
        *   `Authorization: Bearer {admin_token}`
    *   **Query Parameters**:
        *   `days` (integer, optional, default: 7): Number of past days to include in stats (1-30).
*   **Response**:
    *   **Success (200 OK)**: Rate limit statistics (JSON).

### `PUT /api/admin/users/role`
*   **Description**: Updates the role of a specified user.
*   **Request**:
    *   **Headers**:
        *   `Authorization: Bearer {admin_token}`
    *   **Body**: (Likely contains user identifier and new role, e.g.)
        ```json
        {
          "user_id": 123, // or "email": "user@example.com"
          "new_role": "admin" // or "user"
        }
        ```
*   **Response**:
    *   **Success (200 OK)**: Confirmation message or updated user object.

### `GET /api/admin/user-statistics`
*   **Description**: Provides comprehensive statistics about user accounts.
*   **Request**:
    *   **Headers**:
        *   `Authorization: Bearer {admin_token}`
*   **Response**:
    *   **Success (200 OK)**:
        ```json
        {
          "total_users": 100,
          "admin_users": 5,
          "regular_users": 95,
          "active_users_30d": {
            "total": 45,
            "admin": 4,
            "regular": 41
          },
          "timestamp": "2023-11-01T14:30:45.123456"
        }

### `GET /api/admin/users`
*   **Description**: Retrieves a list of all users.
*   **Request**:
    *   **Headers**:
        *   `Authorization: Bearer {admin_token}`
    *   **Query Parameters**:
        *   `skip` (integer, optional, default: 0): Number of users to skip
        *   `limit` (integer, optional, default: 100): Maximum number of users to return
*   **Response**:
    *   **Success (200 OK)**: List of user objects

### `GET /api/admin/online-users`
*   **Description**: Gets the count of currently online users.
*   **Request**:
    *   **Headers**:
        *   `Authorization: Bearer {admin_token}`
    *   **Query Parameters**:
        *   `minutes` (integer, optional, default: 15): Consider users active within this many minutes
*   **Response**:
    *   **Success (200 OK)**:
        ```json
        {
          "online_users": 5,
          "total_users": 100,
          "active_window_minutes": 15,
          "timestamp": "2023-11-01T14:30:45.123456"
        }
        ```

### `GET /api/admin/online-users`
*   **Description**: Gets the count of currently online users.
*   **Request**:
    *   **Headers**:
        *   `Authorization: Bearer {admin_token}`
    *   **Query Parameters**:
        *   `minutes` (integer, optional, default: 15): Consider users active within this many minutes
*   **Response**:
    *   **Success (200 OK)**:
        ```json
        {
          "online_users": 5,
          "total_users": 100,
          "active_window_minutes": 15,
          "timestamp": "2023-11-01T14:30:45.123456"
        }
        ```

### `DELETE /api/admin/users/delete`
*   **Description**: Deletes a user by email or ID. Requires admin authentication.
*   **Request**:
    *   **Headers**:
        *   `Authorization: Bearer {admin_token}`
    *   **Body**: `UserDeleteRequest`
        ```json
        {
          "id": 123,           // Optional: User ID
          "email": "user@example.com"  // Optional: User email
        }
        ```
        Note: At least one of [id](http://_vscodecontentref_/1) or [email](http://_vscodecontentref_/2) must be provided.
*   **Response**:
    *   **Success (200 OK)**:
        ```json
        {
          "detail": "User deleted successfully."
        }
        ```
    *   **Error (404 Not Found)**: If user doesn't exist.
        ```json
        {
          "detail": "User not found."
        }
        ```
    *   **Error (400 Bad Request)**: If neither id nor email is provided.
        ```json
        {
          "detail": "Must provide user id or email."
        }
        ```

## Token (prefix: `/api`)

### `GET /api/validate_token`
*   **Description**: Validates an authentication token.
*   **Request**:
    *   **Headers**:
        *   `Authorization: Bearer {token}`
*   **Response**:
    *   **Success (200 OK)**: User object (`UserOut`) if the token is valid.
    *   **Error (e.g., 401 Unauthorized)**: If the token is invalid or expired.

## Auth (prefix: `/auth`)
Endpoints for handling OAuth authentication flows.

### `GET /auth/google_login`
*   **Description**: Initiates the Google OAuth2 login flow.
*   **Request**: None
*   **Response**:
    *   **Redirect**: Redirects the user to Google's authentication page.

### `GET /auth/callback`
*   **Description**: Handles the callback from Google after user authentication. It exchanges the authorization code for tokens, retrieves user information, creates or updates the user in the database, generates a JWT token, and redirects the user to the frontend.
*   **Request**:
    *   **Query Parameters**: (Provided by Google)
        *   `code` (string): Authorization code from Google.
        *   `state` (string, optional): State parameter for CSRF protection.
*   **Response**:
    *   **Redirect**: Redirects to the frontend application, typically with the JWT token (e.g., as a query parameter or cookie).

## Forms (prefix: `/api/forms`)

### `POST /api/forms/submit`
*   **Description**: Submits data from a contact form.
*   **Request**:
    *   **Body**: `FormSubmissionSchema`
        ```json
        {
          "full_name": "John Doe",
          "email": "john.doe@example.com",
          "subject": "Inquiry about API",
          "message": "Hello, I have a question..."
        }
        ```
*   **Response**:
    *   **Success (200 OK)**: The submitted `FormSubmissionSchema` object with an ID and timestamp.

### `GET /api/forms/submissions`
*   **Description**: Retrieves a list of submitted forms. Requires admin authentication.
*   **Request**:
    *   **Headers**:
        *   `Authorization: Bearer {admin_token}`
    *   **Query Parameters**:
        *   `limit` (integer, optional): Maximum number of submissions to return.
*   **Response**:
    *   **Success (200 OK)**: `List[FormSubmissionSchema]`
        ```json
        [
          {
            "id": 1,
            "full_name": "Jane Doe",
            "email": "jane.doe@example.com",
            "subject": "Feedback",
            "message": "Great service!",
            "created_at": "2023-10-26T10:00:00Z"
          }
          // ... more submissions
        ]
        ```

## Feedback (prefix: `/api/feedback`)

### `POST /api/feedback`
*   **Description**: Submits user feedback related to a telemetry record. Requires active user authentication.
*   **Request**:
    *   **Headers**:
        *   `Authorization: Bearer {token}`
    *   **Body**: `UserFeedbackCreate`
        ```json
        {
          "telemetry_id": "some_request_id_string",
          "rating": 5, // Integer 1-5
          "comment": "The analysis was very accurate.",
          "is_correct": true // boolean, was the original analysis correct?
        }
        ```
*   **Response**:
    *   **Success (200 OK)**: `UserFeedbackOut` (The created feedback object)

### `GET /api/feedback/feedback/latest`
*   **Description**: Retrieves the latest feedback entries, including associated prompt data. Requires admin authentication.
*   **Request**:
    *   **Headers**:
        *   `Authorization: Bearer {admin_token}`
    *   **Query Parameters**:
        *   `limit` (integer, optional, default: 10): Number of feedback entries to return (1-100).
*   **Response**:
    *   **Success (200 OK)**: `List[UserFeedbackWithPromptOut]` (List of feedback objects, each potentially including details from the related telemetry record like the original prompt).