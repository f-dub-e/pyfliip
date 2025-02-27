# Register the user with login infos from "fliip_login.txt" to all the noon class of fliip_gym_name for days set true of noon_classes_to_register
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.webdriver import WebDriver  # For typing

import dateutil.parser as parser
from datetime import datetime, timedelta
import time

fliip_gym_name = "crossfitahuntsic"

noon_classes_to_register = {
    "Monday": False,
    "Tuesday": True,
    "Wednesday": False,
    "Thursday": True,
    "Friday": False,
    "Saturday": False,
    "Sunday": False,
}

# %% Get Login Infos
# TODO: Replace this with env variables
print("Opening fliip_login.txt to get logins...")
with open("fliip_login.txt", "r") as file:
    lines = file.readlines()
    fliip_username = lines[0].replace("\n", "")
    fliip_password = lines[1].replace("\n", "")

# %% Open Page
print(f"Connecting to {fliip_gym_name} Fliip page to log {fliip_username}...")

# Set up the Chrome WebDriver (Make sure you have downloaded chromedriver)
driver = webdriver.Chrome()

# Define the WebDriverWait for waiting for elements
wait = WebDriverWait(driver, timeout=5)  # seconds

# Go to the Fliip login page
driver.get(f"https://{fliip_gym_name}.fliipapp.com/home/login")

# Wait for the page to load and click refuse all privacy button
reject_button = wait.until(
    EC.element_to_be_clickable(
        (By.XPATH, "/html/body/div[2]/div/div/div/div[2]/button[2]")
    )
)
reject_button.click()

# %% Login on Fliip
# Find the username and password input fields and log in
username_input = driver.find_element(By.ID, "username")
password_input = driver.find_element(By.ID, "password")

username_input.send_keys(fliip_username)  # Replace with your actual username
password_input.send_keys(fliip_password)  # Replace with your actual password

# Submit the form
password_input.send_keys(Keys.RETURN)

# Wait to the login to occur and change to English to properly parse date strings
en_language_button = wait.until(
    EC.element_to_be_clickable((By.XPATH, '//*[@id="change_language"]/div/button'))
)
en_language_button.click()

# %% Registering Loop


# Register to noon class function
# Monday is weekday==0.
def register_noon_weekday_class(
    driver: WebDriver, weekday_to_register: int, current_calendar_page_date: datetime
):
    max_hours_in_future_to_register = 336
    # Noon class id from the "class-block-action-icon subscribe-class-icon  class-action-top-lg" on-click register parameters
    noon_class_id = {
        0: "764284",  # Monday
        1: "764296",  # Tuesday
        2: "764307",  # Wednesday
        3: "755904",  # Thursday
        4: "764327",  # Friday
        5: "TBD",  # Saturday
        6: "TBD",  # Sunday
    }
    if noon_class_id[weekday_to_register] == "TBD":
        raise NotImplementedError(
            f"Unsupported weekday! (Noon class of weekday {weekday_to_register} without known ID!)"
        )
    # Click on the "+"" button on the date to register
    # Calculate how many days to subtract from current calandar page date to get to weekday
    days_to_weekday = current_calendar_page_date.weekday() - weekday_to_register
    calendar_page_weekday = current_calendar_page_date - timedelta(days=days_to_weekday)
    calendar_page_weekday = calendar_page_weekday.replace(hour=12)  # Noon class
    if calendar_page_weekday < datetime.now():
        # Class in the past, return and skip
        return
    if (
        calendar_page_weekday - datetime.now()
    ).total_seconds() >= max_hours_in_future_to_register * 3600:
        # Too far in future to register yet, return and skip
        return
    calendar_page_weekday_str = calendar_page_weekday.strftime(f"%Y-%m-%d")
    register_button = driver.find_element(
        By.XPATH,
        f'//*[@id="{noon_class_id[weekday_to_register]},{calendar_page_weekday_str}"]/p/i',
    )
    register_button.click()

    try:
        # Register or Waiting List Modal Dialog
        popup_window = wait.until(
            EC.visibility_of_element_located((By.ID, "book_confirm_modal"))
        )
        title = driver.find_element(By.ID, "title")
    except:
        try:
            # Cancel Registration Modal Dialog Type 1
            popup_window_id = "modal-unregister"
            popup_window = wait.until(
                EC.visibility_of_element_located((By.ID, popup_window_id))
            )
            title = driver.find_element(By.ID, "unreg-title")
        except:
            # Cancel Registration Modal Dialog Type 2
            popup_window_id = "myModal_unreg_waiting"
            popup_window = wait.until(
                EC.visibility_of_element_located((By.ID, popup_window_id))
            )
            title = driver.find_element(By.ID, "title3")

    if "cancel" in title.text.lower():
        # Already registered, close window and return
        try:
            close_button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, f'//*[@id="{popup_window_id}"]/div/div/div[1]/button')
                )
            )

        except:
            close_button = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "close"))
            )
        close_button.click()

        popup_window = wait.until(
            EC.invisibility_of_element_located((By.ID, popup_window_id))
        )

        return

    # Click on the class confirm button
    confirm_button = wait.until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="confirm"]'))
    )
    confirm_button.click()

    # Wait for the success message pop up
    alert = wait.until(
        EC.text_to_be_present_in_element(
            (By.XPATH, '//*[@id="modal_alert"]/div/div/div[1]/h4'), "Message"
        )
    )
    # Click on the exit on the success message
    exit_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="modal_alert"]/div/div/div[1]/button')
        )
    )
    exit_button.click()
    return


# Date in week scrolling header should be today at calendar page first loading
expected_date = datetime.now().date()

# Change the calendar to two weeks later from now
for x in range(0, 3):
    # Check current calendar week page date against expected date
    # Format the expected date to the expected format
    expected_date_str = expected_date.strftime(f"%A %#d %b, %Y")
    # Wait for the proper week page load in the calendar
    try:
        current_date_correct = wait.until(
            EC.text_to_be_present_in_element((By.ID, "current-date"), expected_date_str)
        )
        if not current_date_correct:
            raise RuntimeError(f"Unexpected page! (expected {expected_date_str})")
    except:
        raise RuntimeError(f"Unexpected page! (expected {expected_date_str})")
    # Get current calendar page date
    current_calendar_page_date = driver.find_element(By.ID, "current-date")
    current_calendar_page_date = parser.parse(current_calendar_page_date.text)

    for day in noon_classes_to_register:
        if noon_classes_to_register[day]:
            weekday_number = time.strptime(day, "%A").tm_wday
            register_noon_weekday_class(
                driver=driver,
                current_calendar_page_date=current_calendar_page_date,
                weekday_to_register=weekday_number,
            )

    # Change the calendar week page to next week
    # Find and click the next week button
    next_week_button = wait.until(EC.element_to_be_clickable((By.ID, "next_week")))
    next_week_button.click()
    try:
        # Wait for button staleness (page refresh)
        wait.until(EC.staleness_of(next_week_button))
    except:
        pass
    # Add a week for the next expected date
    expected_date = expected_date + timedelta(days=7)


driver.quit()

print(f"Registration done for the user at noon!")
