import json
import sys
import random
from typing import List, Optional
from enum import Enum

def roll_dice():
    return random.randint(1, 6)

class EventStatus(Enum):
    UNKNOWN = "unknown"
    PASS = "pass"
    FAIL = "fail"
    PARTIAL_PASS = "partial_pass"


class Statistic:
    def __init__(self, name: str, value: int = 0, description: str = "", min_value: int = 0, max_value: int = 100):
        self.name = name
        self.value = value
        self.description = description
        self.min_value = min_value
        self.max_value = max_value

    def __str__(self):
        return f"{self.name}: {self.value}"

    def modify(self, amount: int):
        self.value = max(self.min_value, min(self.max_value, self.value + amount))

class Character:
    def __init__(self, name: str):
        self.name = name
        self.statistics = []

    def __str__(self):
        return f"Character: {self.name}" + f" ({type(self).__name__})" + f"\nStats: {', '.join([str(stat) for stat in self.statistics])}"

    def get_stats(self):
        return self.statistics # Extend this list if there are more stats


class Professor(Character):
    def __init__(self, name: str = "Unnamed"):
        super().__init__(name)
        self.strength = Statistic("Strength", value=10, description="Physical power of the professor.")
        self.statistics.append(self.strength)
        self.intelligence = Statistic("Intelligence", value=15, description="Professor's cognitive ability.")
        self.statistics.append(self.intelligence)
        self.agility = Statistic("Agility", value=8, description="Professor's agility in movement.")
        self.statistics.append(self.agility)



class Student(Character):
    def __init__(self, name: str = "Unnamed"):
        super().__init__(name)
        self.strength = Statistic("Strength", value=5, description="Physical power of the student.")
        self.statistics.append(self.strength)
        self.intelligence = Statistic("Intelligence", value=10, description="Student's cognitive ability.")
        self.statistics.append(self.intelligence)
        self.agility = Statistic("Agility", value=12, description="Student's agility in movement.")
        self.statistics.append(self.agility)




class Event:
    def __init__(self, data: dict):
        self.primary_attribute = data['primary_attribute']
        self.secondary_attribute = data['secondary_attribute']
        self.prompt_text = data['prompt_text']
        self.options = data['options']
        self.pass_message = data['pass']['message']
        self.fail_message = data['fail']['message']
        self.partial_pass_message = data['partial_pass']['message']
        self.status = EventStatus.UNKNOWN
        self.is_voldemort_event = data.get('is_voldemort_event', False)

    def execute(self, character: Character, parser):
        print(f"Dumbledore: {self.prompt_text}")
        print("What will you do?")
        for idx, option in enumerate(self.options):
            print(f"{idx + 1}. {option['choice_text']}")

        choice = int(parser.parse("Enter the number of your choice: ")) - 1
        selected_option = self.options[choice]
        chosen_stat_name = selected_option['associated_stat']

        chosen_stat = next(stat for stat in character.get_stats() if stat.name == chosen_stat_name)

        self.resolve_choice(character, chosen_stat)

    def resolve_choice(self, character: Character, chosen_stat: Statistic):
        dice_roll = roll_dice()
        print(f"Dice roll: {dice_roll}")

        success_threshold = 4
        if chosen_stat.value >= 10:
            success_threshold -= 1
        print(f"Attempting to solve the challenge with {chosen_stat.name}...")

        if dice_roll >= success_threshold and chosen_stat.name == self.primary_attribute:
            self.status = EventStatus.PASS
            print(self.pass_message)
        elif dice_roll >= success_threshold - 1 and chosen_stat.name == self.secondary_attribute:
            self.status = EventStatus.PARTIAL_PASS
            print(self.partial_pass_message)
        else:
            self.status = EventStatus.FAIL
            print(f"{character.name} attempted to use {chosen_stat.name} but failed.")
            print(self.fail_message)


class Location:
    def __init__(self, events: List[Event]):
        self.events = events

    def get_event(self) -> Event:
        return random.choice(self.events)

class Game:
    def __init__(self, parser, character: Character, locations: List[Location]):
        self.parser = parser
        self.character = character
        self.locations = locations
        self.continue_playing = True
        self.voldemort_defeated = False
        self.events_completed = 0
        self.required_events_to_trigger_battle = 3

    def start(self):
        while self.continue_playing:
            location = random.choice(self.locations)
            regular_events = [event for event in location.events if not event.is_voldemort_event]
            event = random.choice(regular_events)
            event.execute(self.character, self.parser)

            if event.status == EventStatus.PASS:
                self.events_completed += 1
                print(f"Completed events: {self.events_completed}/{self.required_events_to_trigger_battle}")
            if self.events_completed >= self.required_events_to_trigger_battle:
                self.voldemort_battle()
                break
        print("Game Over.")
    
    def voldemort_battle(self):
        print("Dumbledore: This it it... your final battle against Voldemort!")
        rounds = 2
        success_count = 0

        location = random.choice(self.locations)
        voldemort_events = [event for event in location.events if event.is_voldemort_event]

        for _ in range(rounds):
            event = random.choice(voldemort_events)
            event.execute(self.character, self.parser)

            if event.status == EventStatus.PASS:
                success_count += 1
            elif event.status == EventStatus.FAIL:
                success_count -= 1
        
            if success_count > 0:
                print(f"Well done! You have the upper hand over Voldemort!")
            else:
                print(f"Voldemort is gaining the upper hand")

        if success_count > 0:
            print("Congratulations! You have defeated Voldemort!")
            self.voldemort_defeated = True
        else:
            print("Voldemort has defeated you... Better luck next time.")

        self.continue_playing = False

class UserInputParser:
    def parse(self, prompt: str) -> str:
        return input(prompt)

    def select_party_member(self, party: List[Character]) -> Character:
        print("Choose a party member:")
        for idx, member in enumerate(party):
            print(f"{idx + 1}. {member.name}")
        choice = int(self.parse("Enter the number of the chosen party member: ")) - 1
        return party[choice]

    def select_stat(self, character: Character) -> Statistic:
        print(f"Choose a stat for {character.name}:")
        stats = character.get_stats()
        for idx, stat in enumerate(stats):
            print(f"{idx + 1}. {stat.name} ({stat.value})")
        choice = int(self.parse("Enter the number of the stat to use: ")) - 1
        return stats[choice]


def load_events_from_json(file_path: str) -> List[Event]:
    with open(file_path, 'r') as file:
        data = json.load(file)
    return [Event(event_data) for event_data in data]


def start_game():
    parser = UserInputParser()

    print("Dumbledore: Welcome, young wizard! The path ahead is filled with challenges, but I have no doubt that you are up to the task.")

    character_names = {
        "1": "Harry Potter",
        "2": "Hermione Granger",
        "3": "Ron Weasley"
    }

    characters: List[Character] = [Student(name) for name in character_names.values()]

    print("Welcome to the adventure! Choose your character:")
    for number, character in enumerate(characters, start=1):
        print(f"{number}. {character.name}")

    while True:
        character_choice = input("Enter the number or name of the character you want to play as: ").strip().lower()

        # Check if the input is a valid number
        if character_choice in character_names:
            chosen_character = next(character for character in characters if character.name.lower() == character_names[character_choice].lower())
            break  # Exit the loop after a valid choice
        # Check if the input is a valid character name
        elif character_choice in (name.lower() for name in character_names.values()):
            chosen_character = next(character for character in characters if character.name.lower() == character_choice)
            break  # Exit the loop after a valid choice
        else:
            print("Invalid input. Please enter either the number or name of a character (Harry Potter, Hermione Granger, Ron Weasley).")

    # Proceed with the chosen character
    print(f"You have chosen: {chosen_character.name}")

    events_location_1 = load_events_from_json('project_code/location_events/location_1.json')
    events_location_2 = load_events_from_json('project_code/location_events/location_2.json')

    all_events = events_location_1 + events_location_2
    locations = [Location(all_events)]
    game = Game(parser, chosen_character, locations)
    game.start()

if __name__ == '__main__':
    start_game()
