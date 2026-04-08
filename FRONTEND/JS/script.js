// Splash → Login after 2 seconds
setTimeout(() => {
    showScreen("login");
}, 2000);

// Helper function to switch screens
function showScreen(id) {
    document.querySelectorAll(".container, #splash").forEach(el => {
        el.classList.remove("active");
    });
    document.getElementById(id).classList.add("active");
}

// L2 - Send OTP (Mock)
function sendOTP() {
    let phone = document.getElementById("phone").value;

    if (phone.length < 10) {
        alert("Enter valid phone number");
        return;
    }

    localStorage.setItem("phone", phone);

    // Mock OTP
    localStorage.setItem("otp", "123456");

    alert("OTP sent: 123456");
    showScreen("otpScreen");
}

// L3 - Verify OTP
function verifyOTP() {
    let entered = document.getElementById("otp").value;
    let realOTP = localStorage.getItem("otp");

    if (entered === realOTP) {

        // L7 - Returning user
        let role = localStorage.getItem("role");

        if (role) {
            goToDashboard(role);
        } else {
            showScreen("roleScreen");
        }

    } else {
        alert("Invalid OTP");
    }
}

// L4 + L8 - Role selection & lock
function setRole(role) {
    if (localStorage.getItem("role")) {
        alert("Role cannot be changed!");
        return;
    }

    localStorage.setItem("role", role);
    goToDashboard(role);
}

// Dashboard
function goToDashboard(role) {
    document.getElementById("welcome").innerText =
        "Welcome " + role.toUpperCase();

    showScreen("dashboard");
}

// Auto-login if user already exists
window.onload = () => {
    let role = localStorage.getItem("role");
    let phone = localStorage.getItem("phone");

    if (role && phone) {
        setTimeout(() => {
            goToDashboard(role);
        }, 2000);
    }
};