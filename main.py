import flet as ft
import requests
import sqlite3
import hashlib
import os
from datetime import datetime
import json

# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8008/predict"
DB_PATH = "sheep_app.db"

# --- DATABASE SETUP ---
def init_database():
    """Initialize SQLite database for user authentication and scan history"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # New table for scan history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            weight_kg REAL NOT NULL,
            confidence REAL NOT NULL,
            status TEXT NOT NULL,
            image_name TEXT,
            scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, email, password):
    """Create a new user account"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        
        conn.commit()
        conn.close()
        return True, "Account created successfully!"
    except sqlite3.IntegrityError:
        return False, "Username or email already exists"
    except Exception as e:
        return False, f"Error: {str(e)}"

def verify_user(email, password):
    """Verify user credentials"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        password_hash = hash_password(password)
        cursor.execute(
            "SELECT id, username, email FROM users WHERE email = ? AND password_hash = ?",
            (email, password_hash)
        )
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return True, {"id": user[0], "username": user[1], "email": user[2]}
        else:
            return False, None
    except Exception as e:
        return False, None

def save_scan_result(user_id, weight_kg, confidence, status, image_name):
    """Save scan result to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO scan_history (user_id, weight_kg, confidence, status, image_name) VALUES (?, ?, ?, ?, ?)",
            (user_id, weight_kg, confidence, status, image_name)
        )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving scan result: {e}")
        return False

def get_user_scans(user_id, limit=10):
    """Retrieve user's scan history"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT id, weight_kg, confidence, status, image_name, scan_date 
               FROM scan_history 
               WHERE user_id = ? 
               ORDER BY scan_date DESC 
               LIMIT ?""",
            (user_id, limit)
        )
        
        scans = cursor.fetchall()
        conn.close()
        return scans
    except Exception as e:
        print(f"Error retrieving scans: {e}")
        return []

def get_user_stats(user_id):
    """Get user statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Total scans
        cursor.execute("SELECT COUNT(*) FROM scan_history WHERE user_id = ?", (user_id,))
        total_scans = cursor.fetchone()[0]
        
        # Average confidence
        cursor.execute("SELECT AVG(confidence) FROM scan_history WHERE user_id = ?", (user_id,))
        avg_confidence = cursor.fetchone()[0] or 0
        
        # This week scans
        cursor.execute(
            "SELECT COUNT(*) FROM scan_history WHERE user_id = ? AND scan_date >= date('now', '-7 days')",
            (user_id,)
        )
        week_scans = cursor.fetchone()[0]
        
        conn.close()
        return {
            "total_scans": total_scans,
            "avg_confidence": round(avg_confidence, 1),
            "week_scans": week_scans
        }
    except Exception as e:
        print(f"Error getting stats: {e}")
        return {"total_scans": 0, "avg_confidence": 0, "week_scans": 0}

def main(page: ft.Page):
    # Initialize database
    init_database()
    
    # --- 1. App Setup ---
    page.title = "Sheep Weight AI"
    page.padding = 0
    page.bgcolor = "#0F1419"
    page.theme_mode = ft.ThemeMode.DARK
    
    page.fonts = {"Poppins": "https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap"}
    page.theme = ft.Theme(font_family="Poppins")

    # --- 2. Session State ---
    current_user = {"logged_in": False, "data": None}
    user_stats = {"total_scans": 0, "avg_confidence": 0, "week_scans": 0}
    scan_history = []

    # --- 3. Premium Design System ---
    NEON_CYAN = "#00FFD1"
    ELECTRIC_BLUE = "#0EA5E9"
    VIVID_PURPLE = "#A855F7"
    HOT_PINK = "#EC4899"
    LIME_GREEN = "#84CC16"
    
    DARK_BG = "#0F1419"
    CARD_BG = "#1A1F2E"
    SURFACE = "#141B26"
    WHITE = "#FFFFFF"
    TEXT_PRIMARY = "#F1F5F9"
    TEXT_SECONDARY = "#94A3B8"
    TEXT_MUTED = "#64748B"
    BORDER_COLOR = "#2D3748"
    
    CYAN_GLOW = ft.LinearGradient(
        begin=ft.alignment.top_left,
        end=ft.alignment.bottom_right,
        colors=["#00FFD1", "#0EA5E9", "#3B82F6"]
    )
    PURPLE_GLOW = ft.LinearGradient(
        begin=ft.alignment.top_left,
        end=ft.alignment.bottom_right,
        colors=["#A855F7", "#EC4899", "#F97316"]
    )
    MESH_GRADIENT = ft.LinearGradient(
        begin=ft.alignment.top_left,
        end=ft.alignment.bottom_right,
        colors=["#1A1F2E", "#141B26", "#0F1419"]
    )
    
    CARD_SHADOW = [
        ft.BoxShadow(blur_radius=30, color="#00000040", offset=ft.Offset(0, 10), spread_radius=-5),
        ft.BoxShadow(blur_radius=60, color="#00FFD120", offset=ft.Offset(0, 20), spread_radius=-10)
    ]
    BUTTON_SHADOW = [
        ft.BoxShadow(blur_radius=25, color="#00FFD140", offset=ft.Offset(0, 8), spread_radius=0)
    ]
    GLOW_EFFECT = [
        ft.BoxShadow(blur_radius=40, color="#00FFD130", offset=ft.Offset(0, 0), spread_radius=0)
    ]

    # --- 4. LOGIC & STATE ---
    result_text = ft.Text("Ready to scan", size=32, weight="bold", color=NEON_CYAN)
    details_text = ft.Text("Select an image to start analysis", size=15, color=TEXT_SECONDARY)
    loading_ring = ft.ProgressRing(visible=False, width=40, height=40, color=NEON_CYAN, stroke_width=4)

    def process_upload(file_path):
        """Enhanced backend communication with better error handling"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return {"success": False, "error": "File not found"}
            
            # Open and send file
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "image/jpeg")}
                
                # Make request with timeout
                response = requests.post(API_URL, files=files, timeout=10)
            
            # Check response status
            if response.status_code == 200:
                data = response.json()
                
                # Validate response structure
                if data.get("success", False):
                    return {
                        "success": True,
                        "weight_kg": data.get("weight_kg", 0),
                        "confidence": data.get("confidence", 0),
                        "status": data.get("status", "Unknown"),
                        "image_name": os.path.basename(file_path)
                    }
                else:
                    return {"success": False, "error": data.get("error", "Unknown error")}
            else:
                return {"success": False, "error": f"Server error: {response.status_code}"}
                
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timeout - server took too long"}
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Connection error - is the backend running?"}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            
            # Update UI to show processing
            result_text.value = "Analyzing..."
            details_text.value = "AI is processing your image..."
            loading_ring.visible = True
            page.update()

            # Process the upload
            result = process_upload(file_path)
            
            # Hide loading indicator
            loading_ring.visible = False
            
            if result.get("success"):
                # Extract data
                weight = result["weight_kg"]
                confidence = result["confidence"]
                status = result["status"]
                image_name = result["image_name"]
                
                # Update UI with results
                result_text.value = f"{weight} kg"
                details_text.value = f"{status} • {confidence}% Confidence"
                
                # Save to database if user is logged in
                if current_user["logged_in"]:
                    save_scan_result(
                        current_user["data"]["id"],
                        weight,
                        confidence,
                        status,
                        image_name
                    )
                    
                    # Refresh stats and history
                    refresh_user_data()
                
                # Show success notification
                page.open(ft.SnackBar(
                    ft.Text("✓ Analysis Complete", color=WHITE, weight="bold"),
                    bgcolor="#10B981",
                    behavior=ft.SnackBarBehavior.FLOATING
                ))
            else:
                # Handle error
                error_msg = result.get("error", "Unknown error")
                result_text.value = "Analysis Failed"
                details_text.value = error_msg
                
                # Show error notification
                page.open(ft.SnackBar(
                    ft.Text(f"✗ {error_msg}", color=WHITE, weight="bold"),
                    bgcolor="#EF4444",
                    behavior=ft.SnackBarBehavior.FLOATING
                ))
            
            page.update()

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    def refresh_user_data():
        """Refresh user statistics and scan history"""
        if current_user["logged_in"]:
            nonlocal user_stats, scan_history
            user_stats = get_user_stats(current_user["data"]["id"])
            scan_history = get_user_scans(current_user["data"]["id"])
            build_home()
            build_history()
            page.update()

    # --- 5. PREMIUM UI COMPONENTS ---
    
    def _premium_card(content, gradient=None, has_glow=False, padding=30):
        return ft.Container(
            content=content,
            bgcolor=CARD_BG if not gradient else None,
            gradient=gradient,
            border=ft.border.all(1, "#FFFFFF08"),
            border_radius=28,
            padding=padding,
            shadow=CARD_SHADOW if has_glow else [CARD_SHADOW[0]]
        )

    def _stat_card(icon, value, label, color, gradient):
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(icon, size=32, color=WHITE),
                    gradient=gradient,
                    padding=18,
                    border_radius=20,
                    shadow=GLOW_EFFECT
                ),
                ft.Container(height=12),
                ft.Text(str(value), size=28, weight="bold", color=TEXT_PRIMARY),
                ft.Text(label, size=13, color=TEXT_SECONDARY, weight="w500")
            ], horizontal_alignment="center", spacing=0),
            bgcolor=SURFACE,
            border=ft.border.all(1, BORDER_COLOR),
            border_radius=24,
            padding=20,
            expand=True
        )

    def _feature_card(icon, title, subtitle, badge=None):
        badge_widget = None
        if badge:
            badge_widget = ft.Container(
                content=ft.Text(badge, size=10, weight="bold", color=DARK_BG),
                bgcolor=NEON_CYAN,
                padding=ft.padding.symmetric(horizontal=10, vertical=5),
                border_radius=12
            )
        
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon, size=26, color=NEON_CYAN),
                    bgcolor="#00FFD115",
                    border=ft.border.all(1, "#00FFD130"),
                    padding=16,
                    border_radius=18
                ),
                ft.Container(width=16),
                ft.Column([
                    ft.Text(title, weight="w600", size=16, color=TEXT_PRIMARY),
                    ft.Text(subtitle, size=13, color=TEXT_SECONDARY)
                ], spacing=4, expand=True),
                badge_widget if badge else ft.Icon("chevron_right", size=22, color=TEXT_MUTED)
            ], alignment="center"),
            bgcolor=SURFACE,
            border=ft.border.all(1, BORDER_COLOR),
            border_radius=20,
            padding=20,
            margin=ft.margin.only(bottom=14)
        )

    def _action_button(text, icon, gradient, on_click, is_primary=True):
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=WHITE if is_primary else TEXT_PRIMARY, size=26),
                ft.Container(width=12),
                ft.Text(text, color=WHITE if is_primary else TEXT_PRIMARY, weight="bold", size=17)
            ], alignment="center"),
            gradient=gradient if is_primary else None,
            bgcolor=SURFACE if not is_primary else None,
            border=ft.border.all(1.5, BORDER_COLOR) if not is_primary else None,
            border_radius=20,
            padding=22,
            shadow=BUTTON_SHADOW if is_primary else None,
            on_click=on_click
        )

    # --- 6. VIEW CONTAINERS ---
    home_view = ft.Container(expand=True)
    analyze_view = ft.Container(expand=True)
    history_view = ft.Container(expand=True)
    auth_view = ft.Container(expand=True)

    # Authentication State
    is_login_mode = [True]

    def handle_logout():
        current_user["logged_in"] = False
        current_user["data"] = None
        
        # Reset stats
        nonlocal user_stats, scan_history
        user_stats = {"total_scans": 0, "avg_confidence": 0, "week_scans": 0}
        scan_history = []
        
        # Rebuild all views
        build_home()
        build_analyze()
        build_auth()
        build_history()
        
        # Go to home screen
        switch_tab(0)
        
        page.open(ft.SnackBar(
            ft.Text("✓ Logged out successfully", color=WHITE, weight="bold"),
            bgcolor="#10B981",
            behavior=ft.SnackBarBehavior.FLOATING
        ))
        page.update()

    # Build Home View
    def build_home():
        stats = user_stats if current_user["logged_in"] else {"total_scans": 542, "avg_confidence": 95, "week_scans": 12}
        
        home_view.content = ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Container(height=60),
                    ft.Row([
                        ft.Column([
                            ft.Row([
                                ft.Text("👋", size=24),
                                ft.Text("Welcome back" if current_user["logged_in"] else "Welcome", color=TEXT_SECONDARY, size=14, weight="w500")
                            ], spacing=8),
                            ft.Container(height=4),
                            ft.Text(current_user["data"]["username"] if current_user["logged_in"] else "Guest", color=TEXT_PRIMARY, size=32, weight="bold")
                        ], spacing=0),
                        ft.Container(
                            content=ft.Icon("notifications_outlined", color=NEON_CYAN, size=26),
                            bgcolor="#00FFD115",
                            border=ft.border.all(1, "#00FFD130"),
                            padding=14,
                            border_radius=16
                        )
                    ], alignment="spaceBetween"),
                    ft.Container(height=24),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon("auto_awesome", size=16, color=DARK_BG),
                            ft.Text("AI POWERED ANALYSIS", size=12, weight="bold", color=DARK_BG)
                        ], spacing=8),
                        bgcolor=NEON_CYAN,
                        padding=ft.padding.symmetric(horizontal=16, vertical=8),
                        border_radius=20
                    )
                ]),
                padding=28,
                gradient=MESH_GRADIENT
            ),
            
            ft.Container(
                content=ft.Row([
                    _stat_card("insights", stats["total_scans"], "Total Scans", ELECTRIC_BLUE, CYAN_GLOW),
                    _stat_card("verified", f"{stats['avg_confidence']}%", "Accuracy", LIME_GREEN, ft.LinearGradient(
                        begin=ft.alignment.top_left,
                        end=ft.alignment.bottom_right,
                        colors=["#84CC16", "#22C55E"]
                    )),
                    _stat_card("trending_up", stats["week_scans"], "This Week", VIVID_PURPLE, PURPLE_GLOW)
                ], spacing=14),
                padding=ft.padding.symmetric(horizontal=24, vertical=16)
            ),
            
            ft.Container(
                content=_premium_card(
                    ft.Column([
                        ft.Row([
                            ft.Column([
                                ft.Text("Quick Analysis", size=26, weight="bold", color=TEXT_PRIMARY),
                                ft.Container(height=8),
                                ft.Text("Instant AI predictions in seconds", size=15, color=TEXT_SECONDARY)
                            ], expand=True),
                            ft.Container(
                                content=ft.Icon("auto_awesome", color=NEON_CYAN, size=32),
                                padding=16,
                                border_radius=18,
                                bgcolor="#00FFD115",
                                border=ft.border.all(1, "#00FFD130")
                            )
                        ], alignment="start"),
                        ft.Container(height=24),
                        ft.Container(
                            content=ft.Text("Start Analysis" if current_user["logged_in"] else "Sign In to Analyze", weight="bold", color=WHITE, size=17),
                            gradient=CYAN_GLOW,
                            padding=22,
                            border_radius=18,
                            shadow=BUTTON_SHADOW,
                            alignment=ft.alignment.center,
                            on_click=lambda e: switch_tab(1) if current_user["logged_in"] else switch_tab(3)
                        )
                    ])
                ),
                padding=ft.padding.symmetric(horizontal=24)
            ),
            
            ft.Container(height=24),
            
            ft.Container(
                content=ft.Column([
                    ft.Text("Features", size=22, weight="bold", color=TEXT_PRIMARY),
                    ft.Container(height=16),
                    _feature_card("straighten", "Body Measurements", "Auto-extract dimensions", "NEW"),
                    _feature_card("assessment", "CT Data Integration", "Sync with database"),
                    _feature_card("analytics", "Performance Analytics", "Track farm metrics"),
                ]),
                padding=24
            )
        ], scroll="auto", expand=True)

    # Build Analyze View
    def build_analyze():
        if not current_user["logged_in"]:
            analyze_view.content = ft.Column([
                ft.Container(height=150),
                ft.Container(
                    content=_premium_card(
                        ft.Column([
                            ft.Icon("lock_outline", size=80, color=TEXT_MUTED),
                            ft.Container(height=24),
                            ft.Text("Authentication Required", size=28, weight="bold", color=TEXT_PRIMARY, text_align="center"),
                            ft.Container(height=12),
                            ft.Text("Please sign in to use the analysis feature", size=15, color=TEXT_SECONDARY, text_align="center"),
                            ft.Container(height=32),
                            ft.Container(
                                content=ft.Text("Go to Sign In", weight="bold", color=WHITE, size=17),
                                gradient=CYAN_GLOW,
                                padding=22,
                                border_radius=18,
                                shadow=BUTTON_SHADOW,
                                alignment=ft.alignment.center,
                                on_click=lambda e: switch_tab(3)
                            )
                        ], horizontal_alignment="center")
                    ),
                    padding=24
                )
            ], horizontal_alignment="center", expand=True)
            return
        
        analyze_view.content = ft.Column([
            ft.Container(height=60),
            
            ft.Container(
                padding=28,
                content=ft.Column([
                    ft.Text("🎯 New Analysis", size=36, weight="bold", color=TEXT_PRIMARY),
                    ft.Container(height=8),
                    ft.Text("Select a photo to get instant AI predictions", size=15, color=TEXT_SECONDARY)
                ], spacing=0)
            ),
            
            ft.Container(height=8),
            
            ft.Container(
                content=_premium_card(
                    ft.Column([
                        ft.Text("PREDICTION RESULT", size=12, weight="bold", color=TEXT_MUTED),
                        ft.Container(height=20),
                        ft.Row([
                            ft.Column([
                                result_text,
                                ft.Container(height=8),
                                details_text
                            ], expand=True),
                            loading_ring
                        ], alignment="spaceBetween", vertical_alignment="center"),
                        ft.Container(height=20),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon("info_outline", size=16, color=ELECTRIC_BLUE),
                                ft.Text("Results are AI-powered estimates", size=12, color=TEXT_MUTED)
                            ], spacing=8),
                            bgcolor="#0EA5E910",
                            border=ft.border.all(1, "#0EA5E920"),
                            padding=14,
                            border_radius=14
                        )
                    ]),
                    has_glow=True
                ),
                padding=24
            ),
            
            ft.Container(height=32),
            
            ft.Container(
                content=ft.Column([
                    _action_button(
                        "Select Image",
                        "collections",
                        CYAN_GLOW,
                        lambda _: file_picker.pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png"]),
                        is_primary=True
                    ),
                    ft.Container(height=16),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon("check_circle", size=16, color=LIME_GREEN),
                            ft.Text("Backend connected and ready", size=13, color=TEXT_SECONDARY)
                        ], spacing=8),
                        bgcolor="#84CC1610",
                        border=ft.border.all(1, "#84CC1620"),
                        padding=14,
                        border_radius=14
                    )
                ]),
                padding=24
            )
        ], scroll="auto", expand=True)

    # Build History View
    def build_history():
        if not current_user["logged_in"]:
            history_view.content = ft.Column([
                ft.Container(height=150),
                ft.Container(
                    content=_premium_card(
                        ft.Column([
                            ft.Icon("history", size=80, color=TEXT_MUTED),
                            ft.Container(height=24),
                            ft.Text("No History Available", size=28, weight="bold", color=TEXT_PRIMARY, text_align="center"),
                            ft.Container(height=12),
                            ft.Text("Sign in to view your scan history", size=15, color=TEXT_SECONDARY, text_align="center"),
                        ], horizontal_alignment="center")
                    ),
                    padding=24
                )
            ], horizontal_alignment="center", expand=True)
            return
        
        # Build history items from database
        history_items = []
        for scan in scan_history:
            scan_id, weight, confidence, status, image_name, scan_date = scan
            
            # Parse date
            try:
                dt = datetime.strptime(scan_date, "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%b %d, %Y")
            except:
                date_str = scan_date
            
            history_items.append(
                _feature_card(
                    "pets",
                    f"Scan #{scan_id}",
                    f"{date_str} • {weight}kg • {confidence}% confidence",
                    status
                )
            )
        
        if not history_items:
            history_items = [
                ft.Container(
                    content=ft.Column([
                        ft.Icon("inbox", size=60, color=TEXT_MUTED),
                        ft.Container(height=16),
                        ft.Text("No scans yet", size=18, weight="bold", color=TEXT_PRIMARY),
                        ft.Text("Start analyzing to build your history", size=14, color=TEXT_SECONDARY)
                    ], horizontal_alignment="center"),
                    padding=40
                )
            ]
        
        history_view.content = ft.Column([
            ft.Container(height=60),
            
            ft.Container(
                padding=28,
                content=ft.Row([
                    ft.Column([
                        ft.Text("📊 History", size=36, weight="bold", color=TEXT_PRIMARY),
                        ft.Container(height=8),
                        ft.Text(f"{len(scan_history)} total scans", size=15, color=TEXT_SECONDARY)
                    ], expand=True),
                    ft.Container(
                        content=ft.Icon("filter_list", color=NEON_CYAN, size=24),
                        bgcolor="#00FFD115",
                        border=ft.border.all(1, "#00FFD130"),
                        padding=14,
                        border_radius=16
                    )
                ], alignment="spaceBetween")
            ),
            
            ft.Container(height=8),
            
            ft.Container(
                content=ft.Column(history_items),
                padding=24
            )
        ], scroll="auto", expand=True)

    # Build Authentication View
    def build_auth():
        if current_user["logged_in"]:
            auth_view.content = ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Container(height=60),
                        ft.Container(
                            content=ft.Icon("person", size=56, color=WHITE),
                            gradient=PURPLE_GLOW,
                            border=ft.border.all(4, "#FFFFFF20"),
                            padding=32,
                            border_radius=100,
                            shadow=GLOW_EFFECT
                        ),
                        ft.Container(height=20),
                        ft.Text(current_user["data"]["username"], color=TEXT_PRIMARY, weight="bold", size=28),
                        ft.Text(current_user["data"]["email"], color=TEXT_SECONDARY, size=14)
                    ], horizontal_alignment="center"),
                    gradient=MESH_GRADIENT,
                    padding=40,
                    height=320
                ),
                
                ft.Container(
                    content=_premium_card(
                        ft.Row([
                            ft.Column([
                                ft.Icon("insights", color=ELECTRIC_BLUE, size=32),
                                ft.Text(str(user_stats["total_scans"]), weight="bold", size=24, color=TEXT_PRIMARY),
                                ft.Text("Scans", size=12, color=TEXT_SECONDARY)
                            ], horizontal_alignment="center", spacing=6),
                            ft.Container(width=2, height=70, bgcolor=BORDER_COLOR),
                            ft.Column([
                                ft.Icon("verified", color=LIME_GREEN, size=32),
                                ft.Text(f"{user_stats['avg_confidence']}%", weight="bold", size=24, color=TEXT_PRIMARY),
                                ft.Text("Accuracy", size=12, color=TEXT_SECONDARY)
                            ], horizontal_alignment="center", spacing=6),
                            ft.Container(width=2, height=70, bgcolor=BORDER_COLOR),
                            ft.Column([
                                ft.Icon("trending_up", color=VIVID_PURPLE, size=32),
                                ft.Text(str(user_stats["week_scans"]), weight="bold", size=24, color=TEXT_PRIMARY),
                                ft.Text("This Week", size=12, color=TEXT_SECONDARY)
                            ], horizontal_alignment="center", spacing=6),
                        ], alignment="spaceAround"),
                        has_glow=True,
                        padding=24
                    ),
                    margin=ft.margin.only(top=-60, left=24, right=24)
                ),
                
                ft.Container(height=24),
                
                ft.Container(
                    content=ft.Column([
                        _feature_card("settings", "Settings", "App preferences"),
                        _feature_card("notifications", "Notifications", "Manage alerts"),
                        _feature_card("help_outline", "Help & Support", "Get assistance"),
                        ft.Container(
                            content=ft.Row([
                                ft.Container(
                                    content=ft.Icon("logout", size=26, color="#EF4444"),
                                    bgcolor="#EF444415",
                                    border=ft.border.all(1, "#EF444430"),
                                    padding=16,
                                    border_radius=18
                                ),
                                ft.Container(width=16),
                                ft.Column([
                                    ft.Text("Log Out", weight="w600", size=16, color="#EF4444"),
                                    ft.Text("Sign out of account", size=13, color=TEXT_SECONDARY)
                                ], spacing=4, expand=True),
                                ft.Icon("chevron_right", size=22, color=TEXT_MUTED)
                            ], alignment="center"),
                            bgcolor=SURFACE,
                            border=ft.border.all(1, BORDER_COLOR),
                            border_radius=20,
                            padding=20,
                            on_click=lambda e: handle_logout()
                        ),
                    ]),
                    padding=24
                )
            ], scroll="auto", expand=True)
            return
        
        # Sign In / Sign Up Form
        username_field = ft.TextField(
            label="Username",
            hint_text="Enter your username",
            border_color=BORDER_COLOR,
            focused_border_color=NEON_CYAN,
            text_size=15,
            visible=not is_login_mode[0]
        )
        
        email_field = ft.TextField(
            label="Email",
            hint_text="Enter your email",
            border_color=BORDER_COLOR,
            focused_border_color=NEON_CYAN,
            text_size=15,
            keyboard_type=ft.KeyboardType.EMAIL
        )
        
        password_field = ft.TextField(
            label="Password",
            hint_text="Enter your password",
            password=True,
            can_reveal_password=True,
            border_color=BORDER_COLOR,
            focused_border_color=NEON_CYAN,
            text_size=15
        )
        
        error_text = ft.Text("", color="#EF4444", size=13, visible=False)
        
        def handle_auth(e):
            if not is_login_mode[0]:
                # Sign Up
                if not username_field.value or not email_field.value or not password_field.value:
                    error_text.value = "All fields are required"
                    error_text.visible = True
                    page.update()
                    return
                
                success, message = create_user(username_field.value, email_field.value, password_field.value)
                
                if success:
                    error_text.visible = False
                    page.open(ft.SnackBar(
                        ft.Text("✓ Account created! Please sign in.", color=WHITE, weight="bold"),
                        bgcolor="#10B981",
                        behavior=ft.SnackBarBehavior.FLOATING
                    ))
                    toggle_mode(None)
                else:
                    error_text.value = message
                    error_text.visible = True
            else:
                # Sign In
                if not email_field.value or not password_field.value:
                    error_text.value = "Email and password are required"
                    error_text.visible = True
                    page.update()
                    return
                
                success, user_data = verify_user(email_field.value, password_field.value)
                
                if success:
                    current_user["logged_in"] = True
                    current_user["data"] = user_data
                    error_text.visible = False
                    
                    # Load user stats
                    refresh_user_data()
                    
                    # Rebuild all views with new auth state
                    build_home()
                    build_analyze()
                    build_auth()
                    
                    # Switch to home and show success message
                    switch_tab(0)
                    
                    page.open(ft.SnackBar(
                        ft.Text(f"✓ Welcome back, {user_data['username']}!", color=WHITE, weight="bold"),
                        bgcolor="#10B981",
                        behavior=ft.SnackBarBehavior.FLOATING
                    ))
                    page.update()
                else:
                    error_text.value = "Invalid email or password"
                    error_text.visible = True
            
            page.update()
        
        def toggle_mode(e):
            is_login_mode[0] = not is_login_mode[0]
            username_field.visible = not is_login_mode[0]
            error_text.visible = False
            build_auth()
            page.update()
        
        auth_view.content = ft.Column([
            ft.Container(height=60),
            
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Icon("lock_person" if is_login_mode[0] else "person_add", size=64, color=NEON_CYAN),
                        gradient=CYAN_GLOW,
                        padding=24,
                        border_radius=100,
                        shadow=GLOW_EFFECT
                    ),
                    ft.Container(height=24),
                    ft.Text("Welcome Back!" if is_login_mode[0] else "Create Account", size=32, weight="bold", color=TEXT_PRIMARY),
                    ft.Container(height=8),
                    ft.Text("Sign in to continue" if is_login_mode[0] else "Sign up to get started", size=15, color=TEXT_SECONDARY)
                ], horizontal_alignment="center"),
                padding=28
            ),
            
            ft.Container(height=16),
            
            ft.Container(
                content=_premium_card(
                    ft.Column([
                        username_field,
                        ft.Container(height=16),
                        email_field,
                        ft.Container(height=16),
                        password_field,
                        ft.Container(height=8),
                        error_text,
                        ft.Container(height=24),
                        ft.Container(
                            content=ft.Text("Sign In" if is_login_mode[0] else "Sign Up", weight="bold", color=WHITE, size=17),
                            gradient=CYAN_GLOW,
                            padding=22,
                            border_radius=18,
                            shadow=BUTTON_SHADOW,
                            alignment=ft.alignment.center,
                            on_click=handle_auth
                        ),
                        ft.Container(height=16),
                        ft.Row([
                            ft.Text("Don't have an account?" if is_login_mode[0] else "Already have an account?", size=13, color=TEXT_SECONDARY),
                            ft.TextButton(
                                "Sign Up" if is_login_mode[0] else "Sign In",
                                style=ft.ButtonStyle(color=NEON_CYAN, padding=0),
                                on_click=toggle_mode
                            )
                        ], alignment="center")
                    ], spacing=0)
                ),
                padding=24
            )
        ], scroll="auto", expand=True, horizontal_alignment="center")

    # --- 7. NAVIGATION SYSTEM ---
    main_stack = ft.Stack([
        home_view,
        analyze_view,
        history_view,
        auth_view
    ], expand=True)

    def switch_tab(index):
        home_view.visible = False
        analyze_view.visible = False
        history_view.visible = False
        auth_view.visible = False
        
        if index == 0:
            home_view.visible = True
        elif index == 1:
            analyze_view.visible = True
        elif index == 2:
            history_view.visible = True
        elif index == 3:
            auth_view.visible = True
        
        page.navigation_bar.selected_index = index
        page.update()

    # Premium Navigation Bar
    page.navigation_bar = ft.NavigationBar(
        bgcolor=CARD_BG,
        indicator_color="#00FFD120",
        surface_tint_color=NEON_CYAN,
        elevation=0,
        border=ft.border.only(top=ft.BorderSide(1, BORDER_COLOR)),
        height=75,
        selected_index=0,
        label_behavior=ft.NavigationBarLabelBehavior.ONLY_SHOW_SELECTED,
        on_change=lambda e: switch_tab(e.control.selected_index),
        destinations=[
            ft.NavigationBarDestination(icon="home_outlined", selected_icon="home", label="Home"),
            ft.NavigationBarDestination(icon="camera_alt_outlined", selected_icon="camera_alt", label="Analyze"),
            ft.NavigationBarDestination(icon="history", label="History"),
            ft.NavigationBarDestination(icon="person_outline", selected_icon="person", label="Account"),
        ]
    )

    # Initialize all views
    build_home()
    build_analyze()
    build_history()
    build_auth()

    switch_tab(0)
    page.add(main_stack)

ft.app(target=main)