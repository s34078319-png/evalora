
import { useEffect, useRef, useState } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const timerRef = useRef(null);

  // ==========================================================
  // AUTHENTICATION
  // ==========================================================

  const [accessToken, setAccessToken] = useState(
    () => localStorage.getItem("access_token") || ""
  );

  const [tokenInput, setTokenInput] = useState("");

  // ==========================================================
  // SESSION
  // ==========================================================

  const [sessionId, setSessionId] = useState("");

  // ==========================================================
  // WEBCAM
  // ==========================================================

  const [webcamStarted, setWebcamStarted] = useState(false);

  // ==========================================================
  // FACE VERIFICATION
  // ==========================================================

  const [verifying, setVerifying] = useState(false);
  const [verified, setVerified] = useState(false);
  const [verificationMessage, setVerificationMessage] =
    useState("");

  // ==========================================================
  // TIMER
  // ==========================================================

  const [startedAt, setStartedAt] = useState(null);
  const [deadline, setDeadline] = useState(null);
  const [remainingSeconds, setRemainingSeconds] =
    useState(null);

  // ==========================================================
  // ERROR
  // ==========================================================

  const [error, setError] = useState("");

  // ==========================================================
  // SAVE TOKEN
  // ==========================================================

  function saveToken() {
    const token = tokenInput.trim();

    if (!token) {
      setError("Please enter the access token.");
      return;
    }

    localStorage.setItem(
      "access_token",
      token
    );

    setAccessToken(token);

    setError("");

    setVerificationMessage(
      "Authentication token saved successfully."
    );
  }

  // ==========================================================
  // REMOVE TOKEN
  // ==========================================================

  function clearToken() {
    localStorage.removeItem(
      "access_token"
    );

    setAccessToken("");

    setTokenInput("");

    setVerified(false);

    setVerificationMessage("");

    setError("");
  }

  // ==========================================================
  // AUTHENTICATED FETCH
  // ==========================================================

  function getAuthHeaders() {
    const token =
      localStorage.getItem(
        "access_token"
      );

    if (!token) {
      throw new Error(
        "You are not authenticated. Please enter your access token."
      );
    }

    return {
      Authorization:
        `Bearer ${token}`,
    };
  }

  // ==========================================================
  // START WEBCAM
  // ==========================================================

  async function startWebcam() {
    try {
      setError("");

      if (
        !navigator.mediaDevices?.getUserMedia
      ) {
        throw new Error(
          "Your browser does not support webcam access."
        );
      }

      const stream =
        await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: "user",

            width: {
              ideal: 1280,
            },

            height: {
              ideal: 720,
            },
          },

          audio: false,
        });

      streamRef.current =
        stream;

      if (videoRef.current) {
        videoRef.current.srcObject =
          stream;

        await videoRef.current.play();
      }

      setWebcamStarted(true);

    } catch (err) {
      console.error(err);

      setError(
        "Unable to access webcam. Please allow camera permission and try again."
      );
    }
  }

  // ==========================================================
  // STOP WEBCAM
  // ==========================================================

  function stopWebcam() {
    if (streamRef.current) {
      streamRef.current
        .getTracks()
        .forEach((track) => {
          track.stop();
        });

      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject =
        null;
    }

    setWebcamStarted(false);
  }

  // ==========================================================
  // CAPTURE WEBCAM IMAGE
  // ==========================================================

  function captureWebcamImage() {
    const video =
      videoRef.current;

    const canvas =
      canvasRef.current;

    if (!video || !canvas) {
      throw new Error(
        "Webcam is not ready."
      );
    }

    if (
      video.readyState < 2 ||
      video.videoWidth === 0 ||
      video.videoHeight === 0
    ) {
      throw new Error(
        "Webcam image is not ready yet. Please wait a moment."
      );
    }

    canvas.width =
      video.videoWidth;

    canvas.height =
      video.videoHeight;

    const context =
      canvas.getContext("2d");

    context.drawImage(
      video,
      0,
      0,
      canvas.width,
      canvas.height
    );

    return new Promise(
      (resolve, reject) => {
        canvas.toBlob(
          (blob) => {
            if (!blob) {
              reject(
                new Error(
                  "Unable to capture webcam image."
                )
              );

              return;
            }

            resolve(blob);
          },

          "image/jpeg",

          0.9
        );
      }
    );
  }

  // ==========================================================
  // VERIFY FACE
  // ==========================================================

  async function verifyFace() {
    if (!accessToken) {
      setError(
        "Authentication token is missing. Enter your JWT token first."
      );

      return;
    }

    if (!sessionId.trim()) {
      setError(
        "Enter the session ID first."
      );

      return;
    }

    if (!webcamStarted) {
      setError(
        "Start the webcam first."
      );

      return;
    }

    try {
      setError("");

      setVerificationMessage("");

      setVerifying(true);

      const imageBlob =
        await captureWebcamImage();

      const formData =
        new FormData();

      formData.append(
        "live_image",
        imageBlob,
        "webcam.jpg"
      );

      // ------------------------------------------------------
      // GET JWT
      // ------------------------------------------------------

      const headers =
        getAuthHeaders();

      // ------------------------------------------------------
      // SEND FACE VERIFICATION
      // ------------------------------------------------------

      const response =
        await fetch(
          `${API_BASE_URL}/student/sessions/${sessionId}/verify-face`,
          {
            method: "POST",

            headers,

            body: formData,
          }
        );

      const data =
        await response.json();

      // ------------------------------------------------------
      // AUTHENTICATION FAILURE
      // ------------------------------------------------------

      if (response.status === 401) {
        clearToken();

        throw new Error(
          "Authentication failed. Your token is invalid or expired. Please login again and enter a new token."
        );
      }

      // ------------------------------------------------------
      // OTHER BACKEND ERROR
      // ------------------------------------------------------

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Face verification request failed."
        );
      }

      // ------------------------------------------------------
      // FACE FAILED
      // ------------------------------------------------------

      if (!data.verified) {
        setVerified(false);

        setStartedAt(null);

        setDeadline(null);

        setRemainingSeconds(null);

        setVerificationMessage(
          data.message ||
            "Face verification failed. Please try again."
        );

        return;
      }

      // ------------------------------------------------------
      // FACE VERIFIED
      // ------------------------------------------------------

      setVerified(true);

      setVerificationMessage(
        data.message ||
          "Face verified successfully."
      );

      if (data.started_at) {
        setStartedAt(
          new Date(
            data.started_at
          )
        );
      }

      if (data.deadline) {
        const backendDeadline =
          new Date(
            data.deadline
          );

        setDeadline(
          backendDeadline
        );

        updateRemainingTime(
          backendDeadline
        );
      }

    } catch (err) {
      console.error(err);

      setVerificationMessage("");

      setError(
        err.message ||
          "Face verification failed."
      );

    } finally {
      setVerifying(false);
    }
  }

  // ==========================================================
  // UPDATE TIMER
  // ==========================================================

  function updateRemainingTime(
    targetDeadline
  ) {
    const now =
      Date.now();

    const deadlineTime =
      targetDeadline.getTime();

    const difference =
      deadlineTime - now;

    if (difference <= 0) {
      setRemainingSeconds(0);

      return;
    }

    setRemainingSeconds(
      Math.floor(
        difference / 1000
      )
    );
  }

  // ==========================================================
  // TIMER
  // ==========================================================

  useEffect(() => {
    if (
      !deadline ||
      !verified
    ) {
      return;
    }

    updateRemainingTime(
      deadline
    );

    timerRef.current =
      setInterval(() => {
        updateRemainingTime(
          deadline
        );
      }, 1000);

    return () => {
      if (timerRef.current) {
        clearInterval(
          timerRef.current
        );

        timerRef.current = null;
      }
    };
  }, [
    deadline,
    verified,
  ]);

  // ==========================================================
  // FORMAT TIMER
  // ==========================================================

  function formatTime(
    seconds
  ) {
    if (
      seconds === null
    ) {
      return "--:--:--";
    }

    const safeSeconds =
      Math.max(
        0,
        seconds
      );

    const hours =
      Math.floor(
        safeSeconds / 3600
      );

    const minutes =
      Math.floor(
        (safeSeconds % 3600) / 60
      );

    const secs =
      safeSeconds % 60;

    return [
      String(hours).padStart(
        2,
        "0"
      ),

      String(minutes).padStart(
        2,
        "0"
      ),

      String(secs).padStart(
        2,
        "0"
      ),
    ].join(":");
  }

  // ==========================================================
  // CHECK SESSION FROM BACKEND
  // ==========================================================

  useEffect(() => {
    if (
      !sessionId.trim() ||
      !accessToken
    ) {
      return;
    }

    let intervalId =
      null;

    async function checkSession() {
      try {
        const headers =
          getAuthHeaders();

        const response =
          await fetch(
            `${API_BASE_URL}/student/sessions/${sessionId}`,
            {
              method: "GET",

              headers,
            }
          );

        // ----------------------------------------------------
        // AUTHENTICATION FAILURE
        // ----------------------------------------------------

        if (
          response.status === 401
        ) {
          clearToken();

          setError(
            "Authentication expired. Please login again and enter a new token."
          );

          return;
        }

        if (!response.ok) {
          return;
        }

        const data =
          await response.json();

        // ----------------------------------------------------
        // BACKEND HAS ENDED SESSION
        // ----------------------------------------------------

        if (
          data.active === false
        ) {
          setRemainingSeconds(
            0
          );

          setVerificationMessage(
            "Assessment session has ended."
          );

          if (
            timerRef.current
          ) {
            clearInterval(
              timerRef.current
            );

            timerRef.current =
              null;
          }

          return;
        }

        // ----------------------------------------------------
        // UPDATE TIMER FROM BACKEND
        // ----------------------------------------------------

        if (
          data.face_verified &&
          data.deadline
        ) {
          const backendDeadline =
            new Date(
              data.deadline
            );

          setVerified(
            true
          );

          setDeadline(
            backendDeadline
          );

          updateRemainingTime(
            backendDeadline
          );
        }

      } catch (err) {
        console.error(
          "Session check failed:",
          err
        );
      }
    }

    checkSession();

    intervalId =
      setInterval(
        checkSession,
        5000
      );

    return () => {
      if (intervalId) {
        clearInterval(
          intervalId
        );
      }
    };
  }, [
    sessionId,
    accessToken,
  ]);

  // ==========================================================
  // CLEANUP WEBCAM
  // ==========================================================

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current
          .getTracks()
          .forEach(
            (track) => {
              track.stop();
            }
          );
      }

      if (timerRef.current) {
        clearInterval(
          timerRef.current
        );
      }
    };
  }, []);

  // ==========================================================
  // RENDER
  // ==========================================================

  return (
    <div
      style={{
        minHeight:
          "100vh",

        background:
          "#f5f7fb",

        padding:
          "40px 20px",

        fontFamily:
          "Arial, Helvetica, sans-serif",
      }}
    >
      <div
        style={{
          maxWidth:
            "900px",

          margin:
            "0 auto",

          background:
            "#ffffff",

          borderRadius:
            "16px",

          padding:
            "30px",

          boxShadow:
            "0 10px 30px rgba(0,0,0,0.08)",
        }}
      >
        <h1>
          Evalora Student Assessment
        </h1>

        <p>
          Face verification testing
          frontend.
        </p>

        {/* ================================================== */}
        {/* AUTHENTICATION */}
        {/* ================================================== */}

        <div
          style={{
            marginTop:
              "25px",

            padding:
              "20px",

            borderRadius:
              "12px",

            background:
              "#f3f4f6",
          }}
        >
          <h3>
            Authentication
          </h3>

          <p
            style={{
              fontSize:
                "14px",

              color:
                "#4b5563",
            }}
          >
            Login through Swagger first,
            copy the returned
            <strong>
              {" "}
              access_token
            </strong>
            , and paste it here.
          </p>

          <input
            type="password"
            value={tokenInput}
            onChange={(event) =>
              setTokenInput(
                event.target.value
              )
            }
            placeholder="Paste access token here"
            style={{
              width:
                "100%",

              boxSizing:
                "border-box",

              padding:
                "12px",

              borderRadius:
                "8px",

              border:
                "1px solid #ccc",

              fontSize:
                "14px",
            }}
          />

          <div
            style={{
              display:
                "flex",

              gap:
                "10px",

              marginTop:
                "12px",

              flexWrap:
                "wrap",
            }}
          >
            <button
              onClick={
                saveToken
              }
              style={{
                padding:
                  "10px 18px",

                border:
                  "none",

                borderRadius:
                  "8px",

                cursor:
                  "pointer",

                background:
                  "#2563eb",

                color:
                  "#fff",
              }}
            >
              Save Token
            </button>

            <button
              onClick={
                clearToken
              }
              style={{
                padding:
                  "10px 18px",

                border:
                  "none",

                borderRadius:
                  "8px",

                cursor:
                  "pointer",

                background:
                  "#dc2626",

                color:
                  "#fff",
              }}
            >
              Clear Token
            </button>
          </div>

          <div
            style={{
              marginTop:
                "12px",

              padding:
                "10px",

              borderRadius:
                "8px",

              background:
                accessToken
                  ? "#dcfce7"
                  : "#fee2e2",

              color:
                accessToken
                  ? "#166534"
                  : "#991b1b",

              fontSize:
                "14px",
            }}
          >
            {accessToken
              ? "Authenticated token is stored in this browser."
              : "No authentication token stored."}
          </div>
        </div>

        {/* ================================================== */}
        {/* SESSION ID */}
        {/* ================================================== */}

        <div
          style={{
            marginTop:
              "25px",

            marginBottom:
              "20px",
          }}
        >
          <label
            style={{
              display:
                "block",

              fontWeight:
                "bold",

              marginBottom:
                "8px",
            }}
          >
            Session ID
          </label>

          <input
            type="text"
            value={
              sessionId
            }
            onChange={(
              event
            ) =>
              setSessionId(
                event.target.value
              )
            }
            placeholder="Paste session ID here"
            style={{
              width:
                "100%",

              boxSizing:
                "border-box",

              padding:
                "12px",

              borderRadius:
                "8px",

              border:
                "1px solid #ccc",

              fontSize:
                "16px",
            }}
          />
        </div>

        {/* ================================================== */}
        {/* WEBCAM */}
        {/* ================================================== */}

        <div
          style={{
            marginTop:
              "20px",

            textAlign:
              "center",
          }}
        >
          <video
            ref={
              videoRef
            }
            autoPlay
            playsInline
            muted
            style={{
              width:
                "100%",

              maxWidth:
                "700px",

              background:
                "#111",

              borderRadius:
                "12px",

              display:
                webcamStarted
                  ? "block"
                  : "none",

              margin:
                "0 auto",
            }}
          />

          <canvas
            ref={
              canvasRef
            }
            style={{
              display:
                "none",
            }}
          />

          {!webcamStarted && (
            <div
              style={{
                padding:
                  "80px 20px",

                background:
                  "#111",

                color:
                  "#fff",

                borderRadius:
                  "12px",
              }}
            >
              Webcam is not started.
            </div>
          )}
        </div>

        {/* ================================================== */}
        {/* WEBCAM BUTTONS */}
        {/* ================================================== */}

        <div
          style={{
            display:
              "flex",

            gap:
              "12px",

            marginTop:
              "20px",

            justifyContent:
              "center",

            flexWrap:
              "wrap",
          }}
        >
          {!webcamStarted ? (
            <button
              onClick={
                startWebcam
              }
              style={{
                padding:
                  "12px 22px",

                border:
                  "none",

                borderRadius:
                  "8px",

                cursor:
                  "pointer",

                background:
                  "#2563eb",

                color:
                  "#fff",

                fontSize:
                  "16px",
              }}
            >
              Start Webcam
            </button>
          ) : (
            <button
              onClick={
                stopWebcam
              }
              style={{
                padding:
                  "12px 22px",

                border:
                  "none",

                borderRadius:
                  "8px",

                cursor:
                  "pointer",

                background:
                  "#dc2626",

                color:
                  "#fff",

                fontSize:
                  "16px",
              }}
            >
              Stop Webcam
            </button>
          )}

          <button
            onClick={
              verifyFace
            }
            disabled={
              verifying ||
              !webcamStarted ||
              !sessionId.trim() ||
              !accessToken ||
              verified
            }
            style={{
              padding:
                "12px 22px",

              border:
                "none",

              borderRadius:
                "8px",

              cursor:
                verifying ||
                !webcamStarted ||
                !sessionId.trim() ||
                !accessToken ||
                verified
                  ? "not-allowed"
                  : "pointer",

              background:
                verifying ||
                !webcamStarted ||
                !sessionId.trim() ||
                !accessToken ||
                verified
                  ? "#9ca3af"
                  : "#16a34a",

              color:
                "#fff",

              fontSize:
                "16px",
            }}
          >
            {verifying
              ? "Verifying..."
              : verified
              ? "Face Verified"
              : "Verify Face"}
          </button>
        </div>

        {/* ================================================== */}
        {/* ERROR */}
        {/* ================================================== */}

        {error && (
          <div
            style={{
              marginTop:
                "20px",

              padding:
                "14px",

              borderRadius:
                "8px",

              background:
                "#fee2e2",

              color:
                "#991b1b",
            }}
          >
            {error}
          </div>
        )}

        {/* ================================================== */}
        {/* VERIFICATION RESULT */}
        {/* ================================================== */}

        {verificationMessage && (
          <div
            style={{
              marginTop:
                "20px",

              padding:
                "14px",

              borderRadius:
                "8px",

              background:
                verified
                  ? "#dcfce7"
                  : "#fef3c7",

              color:
                verified
                  ? "#166534"
                  : "#92400e",
            }}
          >
            {verificationMessage}
          </div>
        )}

        {/* ================================================== */}
        {/* TIMER */}
        {/* ================================================== */}

        <div
          style={{
            marginTop:
              "30px",

            padding:
              "25px",

            borderRadius:
              "12px",

            background:
              verified
                ? "#111827"
                : "#e5e7eb",

            color:
              verified
                ? "#ffffff"
                : "#374151",

            textAlign:
              "center",
          }}
        >
          <div
            style={{
              fontSize:
                "14px",

              marginBottom:
                "8px",

              textTransform:
                "uppercase",

              letterSpacing:
                "1px",
            }}
          >
            Assessment Timer
          </div>

          <div
            style={{
              fontSize:
                "42px",

              fontWeight:
                "bold",

              fontFamily:
                "monospace",
            }}
          >
            {formatTime(
              remainingSeconds
            )}
          </div>

          {!verified && (
            <p>
              Timer will start only after
              successful face verification.
            </p>
          )}

          {verified &&
            remainingSeconds ===
              0 && (
              <p>
                Assessment time has expired.
              </p>
            )}
        </div>

        {/* ================================================== */}
        {/* SESSION INFORMATION */}
        {/* ================================================== */}

        {verified && (
          <div
            style={{
              marginTop:
                "25px",

              padding:
                "20px",

              background:
                "#f9fafb",

              borderRadius:
                "10px",
            }}
          >
            <h3>
              Session Information
            </h3>

            <p>
              <strong>
                Session ID:
              </strong>{" "}
              {sessionId}
            </p>

            <p>
              <strong>
                Face verified:
              </strong>{" "}
              Yes
            </p>

            {startedAt && (
              <p>
                <strong>
                  Started:
                </strong>{" "}
                {startedAt.toLocaleString()}
              </p>
            )}

            {deadline && (
              <p>
                <strong>
                  Deadline:
                </strong>{" "}
                {deadline.toLocaleString()}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;

