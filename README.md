# AI-Based Parking Management System

A student-friendly web application with HTML/CSS/JavaScript, Python Flask, MySQL, and a CNN built with TensorFlow/Keras. It includes user/admin login, parking slot booking, booking history, admin slot management, and image-based parking-space classification.

## Important demo behavior

- **User login:** any non-empty username and password are accepted. This is deliberately permissive for a college demo and is not secure authentication.
- **Admin login:** default username `admin`, password `Admin@123`. Change these in `.env` before using the project beyond a local demo.
- **Deep learning:** the project includes a real CNN training pipeline. The included generated images are synthetic teaching/demo data. They prove the workflow runs but do not provide meaningful real-world parking accuracy. For a credible final project evaluation, train on a real labeled parking occupancy dataset.
- **Image scope:** the current CNN classifies one cropped parking-space image as occupied/vacant. Detecting multiple slots in one wide parking-lot image requires defining slot regions or adding a detector.
- **Database:** MySQL is needed for persistent bookings and admin slot management. The login page can load without MySQL, but booking features need the database configured.

## A. Requirements

Install:
1. Python 3.10 or 3.11 (recommended for broad TensorFlow compatibility)
2. MySQL Server and MySQL Workbench (or MySQL command line)
3. VS Code (optional)

During MySQL setup, remember the password for your `root` account.

## B. Open Command Prompt in the project folder

Extract the ZIP, then open the extracted `AI_Parking_Management_System` folder. In File Explorer, click the address bar, type `cmd`, and press Enter.

Check Python:
```bat
python --version
```
If that command does not work, try `py --version`.

## C. Create and activate a virtual environment (Windows CMD)

```bat
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

TensorFlow installation can take a while. If pip reports that no compatible TensorFlow version exists, use Python 3.10 or 3.11 64-bit and recreate the virtual environment.

## D. Configure MySQL

1. Start MySQL Server.
2. Open MySQL Workbench and connect to your local server.
3. Open `database/parking.sql`.
4. Execute the full script (lightning bolt). It creates `parking_db`, tables, and 20 demo slots.
5. Copy `.env.example` to a new file named `.env` in the project root.
6. Edit `.env` and enter your MySQL password after `DB_PASSWORD=`. If your root account has no password, leave it blank.

Example `.env`:
```ini
FLASK_SECRET_KEY=use-a-long-random-secret-for-local-development
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin@123
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=YOUR_MYSQL_PASSWORD
DB_NAME=parking_db
```
Do not include quotation marks around values unless you need them.

## E. Train the CNN (required for image predictions)

Run these commands from the project root, with `.venv` activated:

```bat
python deep_learning\generate_demo_dataset.py
python deep_learning\train_cnn.py
```

Training may take several minutes. It saves `deep_learning\model\parking_cnn.keras`. The demo dataset is synthetic, so the model is for verifying integration only. To improve your project, replace the generated dataset with a real dataset, keeping the folder classes `vacant` and `occupied` and the train/validation structure.

## F. Start the website

From the project root:

```bat
python app.py
```

Open the address shown in CMD, normally:
`http://127.0.0.1:5000`

Keep the CMD window open while using the website. Press `Ctrl+C` in that window to stop the server.

## G. Demo credentials

**Admin**
- Username: `admin`
- Password: `Admin@123`

**User**
- Choose User login.
- Enter any non-empty username and password.

## H. Main features

- Login with User/Admin role selection
- Dashboard with slot and booking counts
- CNN image upload and occupancy prediction
- Two-wheeler/four-wheeler slot selection
- Booking with date/time conflict checking
- Booking history and cancellation
- Admin updates slot status and views bookings

## Troubleshooting

- **`python` is not recognized:** reinstall Python and enable “Add Python to PATH”, or use `py` in place of `python`.
- **MySQL connection error:** check MySQL Server is running and `.env` has the correct password/database.
- **Unknown database `parking_db`:** execute `database/parking.sql` in Workbench.
- **No model is trained:** run both CNN commands in section E.
- **Port 5000 is busy:** stop the other application using it, or change the final `app.run(debug=True)` line to `app.run(debug=True, port=5001)` and open port 5001.
- **Images look unfamiliar to the CNN:** expected with the synthetic model. Train with real labeled parking images for actual performance.
