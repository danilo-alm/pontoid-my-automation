from datetime import datetime
from time import sleep
import logging
import sys
import os

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from dotenv import load_dotenv


def main(website: str, date_range: tuple = None):
    logger = get_logger()
    logger.info(f'Starting - {datetime.now()}')
    
    driver = get_driver()
    driver.implicitly_wait(10)
    
    actions = ActionChains(driver)
    wait = WebDriverWait(driver, 120)
    driver.get(website)
    
    login(driver, *get_credentials())
    navigate_to_conteudo_aplicado(driver, actions, wait)
    
    while True:
        table, btn_next = get_table_elements(driver, wait)
        handle_table(driver, table, actions, wait, logger)
        actions.move_to_element(btn_next).click().perform()
    

def get_table_elements(driver, wait):
    table = wait.until(EC.visibility_of(
        driver.find_element(By.ID, 'tabelaConteudoAplicado')
    ))
    table_paginate_next = wait.until(EC.visibility_of(
        driver.find_element(By.XPATH, '//*[@id="tabelaConteudoAplicado_next"]//a')
    ))
    return table, table_paginate_next


def filter_date(date_str, logger):
    if DATE_FROM is None:
        return True

    parsed_date = datetime.strptime(date_str, DATE_FORMAT)
    if parsed_date > DATE_FROM:
        logger.info(f'Processing date {date_str}')
        return True
    
    logger.info(f'Skipping date {date_str}')
    return False


def handle_copy_dialog(date, driver, actions, wait, logger):
    elem = wait.until(EC.visibility_of(
        driver.find_element(By.ID, 'DataAula')
    ))
    sleep(1)
    elem.click()
    elem.send_keys(date)

    elem = driver.find_element(By.ID, 'btnPesquisarTurmasParaCopiarConteudo')
    elem.click()

    input_turmas = driver.find_element(By.XPATH, "//*[@id='s2id_TurmasIds']//input")
    for turma in TURMAS:
        input_turmas.click()

        dropdown = driver.find_element(By.ID, 'select2-drop')
        opts = dropdown.find_elements(By.XPATH, './/ul/li')

        turma_found = False        
        for opt in opts:
            opt_turma = opt.find_elements(By.XPATH, './div')[0].text
            if opt_turma in TURMAS:
                turma_found = True
                clickable = opt.find_element(By.XPATH, './ul/li')
                clickable.click()
                break
        
        if not turma_found:
            logger.error(f'Turma {turma} not found for date {date}')    

    elem = driver.find_element(By.ID, 'btnCopiarConteudoParaTurmas')
    elem.click()
    
    elem = driver.find_element(By.XPATH, "//button[text()='Ok']")
    elem.click()


def handle_table_row(driver, row, actions, wait, logger):
    date_str = wait.until(EC.visibility_of(
        row.find_element(By.XPATH, './/td[1]')
    )).text.strip()
    
    if not date_str:
        logger.error(f'Date is empty for row {row}')
        sys.exit(1)

    if not filter_date(date_str, logger):
        return
    
    link_copy = wait.until(EC.element_to_be_clickable(
        row.find_element(By.XPATH, ".//a[@title='Copia esse conteúdo aplicado para outras turmas']")
    ))
    actions.move_to_element(link_copy).click().perform()
    
    handle_copy_dialog(date_str, driver, actions, wait, logger)
    

def handle_table(driver, table, actions, wait, logger):
    rows = table.find_elements(By.XPATH, './/tr[not(parent::thead)]')
    for row in rows:
        handle_table_row(driver, row, actions, wait, logger)


def get_logger():
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename='myapp.log', level=logging.INFO)
    return logger


def login(driver, user, password):
    elem = driver.find_element(By.ID, 'usuario')
    elem.clear()
    elem.send_keys(user)

    elem = driver.find_element(By.ID, 'senha')
    elem.clear()
    elem.send_keys(password)

    elem = driver.find_element(By.ID, 'btn-entrar')
    elem.click()


def get_credentials():
    user = os.getenv('MYUSER')
    password = os.getenv('PASSWORD')
    return user, password


def get_driver():
    opts = Options()
    opts.add_experimental_option('detach', True)
    driver = webdriver.Chrome(options=opts)
    return driver


def navigate_to_conteudo_aplicado(driver, actions, wait):
    elem = wait.until(EC.element_to_be_clickable(
        driver.find_element(By.CSS_SELECTOR, "a[data-acaonaturma='ConteudoAplicado']")
    ))
    actions.move_to_element(elem).click().perform()

    sleep(1)
    
    elem = wait.until(EC.element_to_be_clickable(
        driver.find_element(By.ID, 'btn-carregar-dados')
    ))
    actions.move_to_element(elem).click().perform()


DATE_FORMAT = '%d/%m/%Y'
DATE_FROM = datetime.strptime('05/03/2024', DATE_FORMAT)  # exclusive
TURMAS = [
    #'1º ANO B - EMEB. MONTEIRO LOBATO',
    '1º ANO C - EMEB. MONTEIRO LOBATO',
    #'1º ANO D - EMEB. MONTEIRO LOBATO'
]

if __name__ == '__main__':
    load_dotenv()
    website = os.getenv('WEBSITE') 
    main(website)