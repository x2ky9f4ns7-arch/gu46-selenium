#!/usr/bin/env python3
"""Selenium automation for Gu-46 list page with manual login."""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


@dataclass(frozen=True)
class Config:
    base_url: str = "https://e-nakl.railway.uz/ecustomer"
    list_url: str = "https://e-nakl.railway.uz/ecustomer/Gu46/ListGu46"
    date_from: str = "2024-01-01"
    date_to: str = "2024-01-31"
    numbers_file: Path = Path("numbers.txt")
    download_dir: Path = Path("downloads")
    pause_seconds: float = 2.5
    wait_seconds: int = 30


def build_driver(download_dir: Path) -> webdriver.Chrome:
    download_dir.mkdir(parents=True, exist_ok=True)
    options = ChromeOptions()
    prefs = {
        "download.default_directory": str(download_dir.resolve()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    options.add_experimental_option("prefs", prefs)
    return webdriver.Chrome(options=options)


def wait_for_manual_login(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    print("Please complete login manually in the browser.")
    print("After login, navigate will continue automatically.")
    input("Press Enter here after you finish logging in...")
    wait.until(lambda drv: "ecustomer" in drv.current_url)


def navigate_to_list(driver: webdriver.Chrome, wait: WebDriverWait, url: str) -> None:
    driver.get(url)
    wait_for_ready_state(driver, wait)


def wait_for_ready_state(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    wait.until(lambda drv: drv.execute_script("return document.readyState") == "complete")


def wait_for_table_rows(wait: WebDriverWait) -> None:
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))


def set_date_filters_once(driver: webdriver.Chrome, wait: WebDriverWait, date_from: str, date_to: str) -> None:
    date_inputs = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='date']"))
    )
    if len(date_inputs) < 2:
        raise RuntimeError("Expected at least two date inputs on the page.")

    date_inputs[0].clear()
    date_inputs[0].send_keys(date_from)
    date_inputs[1].clear()
    date_inputs[1].send_keys(date_to)

    update_button = wait.until(
        EC.element_to_be_clickable(
            (By.XPATH, "//button[contains(., 'Обновить') or contains(., 'Update')]")
        )
    )
    update_button.click()
    wait_for_table_rows(wait)


def find_search_input(driver: webdriver.Chrome, wait: WebDriverWait):
    candidates = [
        (By.CSS_SELECTOR, "input[placeholder*='Поиск']"),
        (By.CSS_SELECTOR, "input[placeholder*='Search']"),
        (By.CSS_SELECTOR, "input[type='search']"),
    ]
    for selector in candidates:
        try:
            return wait.until(EC.presence_of_element_located(selector))
        except TimeoutException:
            continue
    raise RuntimeError("Search input not found.")


def wait_for_502_clear(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    def is_502_present(drv: webdriver.Chrome) -> bool:
        return "502" in drv.page_source or "Bad Gateway" in drv.page_source

    if is_502_present(driver):
        print("502 detected. Waiting before refresh...")
        time.sleep(5)
        driver.refresh()
        wait_for_ready_state(driver, wait)


def download_first_row_pdf(driver: webdriver.Chrome, wait: WebDriverWait) -> None:
    row = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
    link_candidates = row.find_elements(By.XPATH, ".//a[contains(@href, '.pdf')]")
    if not link_candidates:
        link_candidates = row.find_elements(By.XPATH, ".//a[contains(., 'PDF')]")
    if not link_candidates:
        link_candidates = row.find_elements(By.XPATH, ".//button[contains(., 'PDF')]")
    if not link_candidates:
        raise RuntimeError("PDF download link not found in the first row.")
    link_candidates[0].click()


def load_numbers(path: Path) -> Iterable[str]:
    if not path.exists():
        raise FileNotFoundError(f"Numbers file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            value = line.strip()
            if value:
                yield value


def process_numbers(driver: webdriver.Chrome, wait: WebDriverWait, numbers: Iterable[str], pause: float) -> None:
    search_input = find_search_input(driver, wait)
    for number in numbers:
        wait_for_502_clear(driver, wait)
        search_input.clear()
        search_input.send_keys(number)
        wait_for_table_rows(wait)
        download_first_row_pdf(driver, wait)
        time.sleep(pause)


def main() -> int:
    config = Config(
        date_from=os.getenv("GU46_DATE_FROM", "2024-01-01"),
        date_to=os.getenv("GU46_DATE_TO", "2024-01-31"),
        pause_seconds=float(os.getenv("GU46_PAUSE", "2.5")),
    )

    driver = build_driver(config.download_dir)
    wait = WebDriverWait(driver, config.wait_seconds)

    try:
        driver.get(config.base_url)
        wait_for_manual_login(driver, wait)
        navigate_to_list(driver, wait, config.list_url)
        set_date_filters_once(driver, wait, config.date_from, config.date_to)
        numbers = list(load_numbers(config.numbers_file))
        process_numbers(driver, wait, numbers, config.pause_seconds)
    finally:
        driver.quit()

    return 0


if __name__ == "__main__":
    sys.exit(main())
