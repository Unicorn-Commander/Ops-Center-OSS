<#-- UC-1 Pro Custom Registration Redirect -->
<#-- This page redirects to our beautiful signup-flow.html instead of using Keycloak's basic form -->
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url=https://your-domain.com/signup-flow.html">
    <title>Register - UC-1 Pro</title>
    <style>
        body {
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #1a0033 0%, #220044 25%, #0a1929 50%, #3a0e5a 75%, #1a0033 100%);
            background-size: 400% 400%;
            animation: galaxyShift 20s ease infinite;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: white;
        }

        @keyframes galaxyShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .container {
            text-align: center;
            max-width: 500px;
            padding: 2rem;
        }

        .logo {
            width: 100px;
            height: 100px;
            margin: 0 auto 2rem;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #ffd700 100%);
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 3rem;
            box-shadow: 0 0 40px rgba(255, 215, 0, 0.5);
        }

        h1 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        p {
            font-size: 1.1rem;
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 2rem;
        }

        .spinner {
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top: 3px solid #ffd700;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        a {
            color: #ffd700;
            text-decoration: none;
            font-weight: 600;
        }

        a:hover {
            text-decoration: underline;
        }
    </style>
    <script>
        // Immediate redirect
        window.location.replace('https://your-domain.com/signup-flow.html');
    </script>
</head>
<body>
    <div class="container">
        <div class="logo">🦄</div>
        <h1>Redirecting to Sign Up...</h1>
        <p>Taking you to our beautiful registration page</p>
        <div class="spinner"></div>
        <p style="margin-top: 2rem; font-size: 0.9rem;">
            If you are not redirected automatically,
            <a href="https://your-domain.com/signup-flow.html">click here</a>
        </p>
    </div>
</body>
</html>
