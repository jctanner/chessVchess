#!/usr/bin/env python3

import datetime
import time

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


def diff_states(a ,b, abort=True):
    try:
        deltas = []
        for idx,x in enumerate(a):
            if x != b[idx]:
                deltas.append(x)
        return deltas
    except Exception as e:
        print(e)
        if abort:
            raise(e)
    
    return None


def diff_to_move(diff, reverse=False):

    ix1 = 1
    ix2 = 0
    if reverse:
        ix1 = 0
        ix2 = 1

    x1 = diff[ix1][0][0]
    y1 = diff[ix1][0][1]
    x2 = diff[ix2][0][0]
    y2 = diff[ix2][0][1]

    return(x1,y1,x2,y2)


class StateManager:
    history = None

    def __init__(self):
        self.history = []
    
    def update(self, new_state):
        self.history.append((datetime.datetime.now(), new_state))


class ChessDotCom:
    def __init__(self, name):
        self.name = name
        self.sm = StateManager()
        self.driver = webdriver.Chrome(ChromeDriverManager().install())
        self.driver.get('https://www.chess.com/play/computer')
        time.sleep(.5)

    def __repr__(self):
        return f'<ChessDotCom {self.name}>'

    def remove_overlay(self):
        # remove the numbered overly that gets in the way of clicking
        self.driver.execute_script("return document.getElementsByTagName('svg')[0].remove();")

    def set_title(self):
        self.driver.execute_script(f"document.title = '{self.name}'")

    def click_button_by_text(self, btext, lower=True):
        buttons = self.driver.find_elements(By.TAG_NAME, value='button')
        for button in buttons:
            print(f'BUTTON {button.text}')
            this_text = button.text
            if lower:
                this_text = this_text.lower()
            if this_text.strip() == btext:
                button.click()
                time.sleep(.5)
                return
        raise Exception('button not found')
    
    def change_color(self, color='black'):
        # defaults to white
        # white goes first
        cname = f'select-playing-as-radio-{color}'
        self.driver.find_element(By.CLASS_NAME, value=cname).click()
    
    def update_state(self):
        self.sm.update(self.show_state())

    def show_state(self):
        """return the piece coordinates"""

        # 88 total spaces
        # divs go from right to left, top to bottom
        # 8a 8b 8c 8d ...
        # 7a 7b 7c ...
        # 6a 6b ,,,

        # when black:
        # 81 71 61 51 41 31 21 11
        # 82 72 62 52 42 32 22 12
        # ...
        # 87 77 67 57 47 37 27 17
        # 88 78 68 58 48 38 28 18

        for _ in range(20):
            try:
                positions = []

                # enumerate all pieces on the board
                pieces = self.driver.find_elements(By.CLASS_NAME, value='piece')
                for piece in pieces:
                    cnames = piece.get_attribute('class')
                    cnames = cnames.split()
                    cnames = [x.strip() for x in cnames if x.strip()]
                    pname = cnames[1]
                    snumber = int(cnames[2].split('-')[-1])
                    x = int(cnames[2].split('-')[-1][0])
                    y = int(cnames[2].split('-')[-1][1])
                    positions.append(((x, y), pname))
                
                # add empty positions
                for x in range(1,9):
                    for y in range(1,9):
                        if (x,y) not in [z[0] for z in positions]:
                            positions.append(((x,y), None))

                return sorted(positions)
            except Exception as e:
                print(e)
        
        return None

    def move_piece(self, name, stuff):
        pass

    def move_position(self, x1, y1, x2, y2):

        z1 = 'square-' + str(x1) + str(y1)
        z2 = 'square-' + str(x2) + str(y2)

        print(f'MOVE: {self.name} {z1} to {z2}')

        # click on original coordinate div
        z1e = self.driver.find_element(By.CLASS_NAME, value=z1)
        z1e.click()
        
        time.sleep(.5)

        # click on new coordinate div (only visible after previous click)
        dst = self.driver.find_element(By.CLASS_NAME, value=z2)
        actions = ActionChains(self.driver)
        actions.move_to_element(dst).move_by_offset(0, 0).click().perform()


def main():

    # black goes first, so create it first ...
    black = ChessDotCom('black')
    black.click_button_by_text('ok')
    black.click_button_by_text('choose')
    black.change_color()
    black.click_button_by_text('play')
    black.remove_overlay()
    black.set_title()

    white = ChessDotCom('white')
    white.click_button_by_text('ok')
    white.click_button_by_text('choose')
    white.click_button_by_text('play')
    white.remove_overlay()
    white.set_title()

    time.sleep(2)

    move_number = 0
    color = white
    for x in range(1000):

        move_number += 1
        print(f'current color is {color}')

        while not diff_states(white.show_state(), black.show_state(), abort=False):
            print('waiting for change ...')
            time.sleep(.5)
        changes = diff_states(white.show_state(), black.show_state())
        if not changes:
            print('ERROR: NO CHANGE FOUND!')
            import epdb; epdb.st()

        # if there is a piece in the first spot, do not
        # reverse the move ...
        a = changes[0][0]
        b = changes[1][0]
        to_reverse = False
        for spot in color.show_state():
            if spot[1] is None:
                continue
            color_bit = spot[1][0]
            if color_bit != color.name[0]:
                continue
            if spot[0] == a:
                print(f'NOT REVERSING BECAUSE {spot} EXISTS!')
                to_reverse = True
                break

        this_move = diff_to_move(changes, reverse=to_reverse)

        try:
            color.move_position(*this_move)
        except Exception as e:
            print(e)
            print('could not make move!')
            continue

        time.sleep(.5)

        if color.name == 'white':
            color = black
        elif color.name == 'black':
            color = white

    import epdb; epdb.st()


if __name__ == "__main__":
    main()
