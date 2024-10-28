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
        self.inventory = []

    def __str__(self):
        return f"Character: {self.name}" + f" ({type(self).__name__})" + f"\nStats: {', '.join([str(stat) for stat in self.statistics])}"

    def get_stats(self):
        return self.statistics
    
    def add_item_to_inventory(self, item):
        if item.name not in [existing_item.name for existing_item in self.inventory]:
            self.inventory.append(item)
            print(f"{self.name} added {item.name} to their inventory!")

    def use_item(self, item_name):
        for item in self.inventory:
            if item.name.lower() == item_name.lower():
                item.apply_boost(self)
                self.inventory.remove(item)
                return True
        return False


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
        if name == "Harry Potter":
            self.primary_stat = "Agility"
        elif name == "Hermione Granger":
            self.primary_stat = "Intelligence"
        elif name == "Ron Weasley":
            self.primary_stat = "Strength"
        else:
            self.primary_stat = "Intelligence"

        self.strength = Statistic("Strength", value=5, description="Physical power of the student.")
        self.statistics.append(self.strength)
        self.intelligence = Statistic("Intelligence", value=10, description="Student's cognitive ability.")
        self.statistics.append(self.intelligence)
        self.agility = Statistic("Agility", value=12, description="Student's agility in movement.")
        self.statistics.append(self.agility)

class Item:
    def __init__(self, name: str, stat_to_boost: str, boost_amount: int):
        self.name = name
        self.stat_to_boost = stat_to_boost
        self.boost_amount = boost_amount

    def __str__(self):
        return f"Item: {self.name}, Boosts {self.stat_to_boost} by {self.boost_amount}"
    
    def apply_boost(self, character: Character):
        stat = next(stat for stat in character.get_stats() if stat.name == self.stat_to_boost)
        stat.modify(self.boost_amount)
        print(f"{character.name} received {self.name}, boosting {self.stat_to_boost} by {self.boost_amount}!")


class Event:
    def __init__(self, data: dict):
        self.primary_attribute = data['primary_attribute']
        self.secondary_attribute = data['secondary_attribute']
        self.prompt_text = data['prompt_text']
        self.options = data['options']
        self.pass_message = data['pass']['message']
        self.fail_message = data['fail']['message']
        self.partial_pass_message = data.get('partial_pass', {}).get('message', None)
        self.status = EventStatus.UNKNOWN
        self.is_voldemort_event = data.get('is_voldemort_event', False)    

    def execute(self, character: Character, parser):
        print(f"Dumbledore: {self.prompt_text}")
        print("What will you do?")
        for idx, option in enumerate(self.options):
            print(f"{idx + 1}. {option['choice_text']}")

        while True:
            try:
                choice_input = parser.parse("Enter the number of your choice: ")
                choice = int(choice_input) - 1
                if 0 <= choice < len(self.options):
                    break
                else:
                    print("Invalid choice number. Please select a valid option.")
            except ValueError:
                print("Invalid input. Please enter a number corresponding to your choice.")
        
        selected_option = self.options[choice]
        chosen_stat_name = selected_option['associated_stat']

        chosen_stat = next(stat for stat in character.get_stats() if stat.name == chosen_stat_name)

        self.resolve_choice(character, chosen_stat)

        if self.status == EventStatus.PASS:
            self.award_item(character)

    def resolve_choice(self, character: Character, chosen_stat: Statistic):
        dice_roll = roll_dice()
        print(f"Dice roll: {dice_roll}")

        success_threshold = 5
        if chosen_stat.name == character.primary_stat:
            print(f"{character.name} is using their primary stat: {chosen_stat.name}")
            success_threshold -= 1
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
    
    def award_item(self, character: Character):
        if random.random() < 0.1:
            possible_items = [
                Item("Wizard's Cloak", "Agility", 2),
                Item("Book of Spells", "Intelligence", 3),
                Item("Strength Potion", "Strength", 4)
            ]

            available_items = [item for item in possible_items if item.name not in [i.name for i in character.inventory]]
            if available_items:
                awarded_item = random.choice(available_items)
                character.add_item_to_inventory(awarded_item)
                awarded_item.apply_boost(character)
                print(f"You received a new item: {awarded_item.name}!")


class Location:
    def __init__(self, events: List[Event]):
        self.events = events

    def get_event(self) -> Event:
        return random.choice(self.events)

class Game:
    def __init__(self, parser, character: Character, locations: List[Location], battle_events: dict):
        self.parser = parser
        self.character = character
        self.locations = locations
        self.battle_events = battle_events 
        self.continue_playing = True
        self.event_completed = 0
        self.battles = ["Draco", "Snape", "Voldemort"]
        self.current_battle_index = 0

    def start(self):
        while self.continue_playing and self.current_battle_index < len(self.battles):
            self.run_challenges(3)
            self.battle(self.battles[self.current_battle_index])
            self.current_battle_index += 1
        print("Game Over.")

    def run_challenges(self, num_challenges):
        challenges_completed = 0
        while challenges_completed < num_challenges and self.continue_playing:
            location = random.choice(self.locations)
            regular_events = [event for event in location.events if not event.is_voldemort_event]
            event = random.choice(regular_events)
            event.execute(self.character, self.parser)

            if event.status == EventStatus.PASS:
                challenges_completed += 1
                print(f"Challenges completed: {challenges_completed}/{num_challenges}")
            else:
                print("You need to pass the challenge to proceed.")
    
    def battle(self, opponent_name):
        print(f"Dumbledore: Prepare yourself, you are about to face {opponent_name}!")

        battle_events_for_opponent = self.battle_events.get(opponent_name, [])

        rounds = 2
        player_score = 0
        opponent_score = 0

        while player_score < rounds and opponent_score < rounds:
            if self.character.inventory:
                print(f"{self.character.name}'s Inventory: {[item.name for item in self.character.inventory]}")
                use_item = self.parser.parse("Do you want to use an item? Enter the name of the item or 'no': ").strip().lower()

                if use_item != "no":
                    if self.character.use_item(use_item):
                        print(f"{self.character.name} used {use_item}!")
                    else:
                        print(f"{use_item} is not in the inventory.")
            else:
                print(f"{self.character.name} has no items to use.")

            battle_event = random.choice(battle_events_for_opponent)
            print(f"{opponent_name} {battle_event['prompt_text']}")

            print("What will you do?")
            for idx, option in enumerate(battle_event['options']):
                print(f"{idx + 1}. {option['choice_text']}")

            while True:
                try:
                    choice_input = self.parser.parse("Enter the number of your choice: ")
                    choice = int(choice_input) - 1
                    if 0 <= choice < len(battle_event['options']):
                        break
                    else:
                        print("Invalid choice number. Please select a valid option.")
                except ValueError:
                    print("Invalid input. Please enter a number corresponding to your choice.")
                
            selected_option = battle_event.options[choice]
            chosen_stat_name = selected_option['associated_stat']

            chosen_stat = next(stat for stat in self.character.get_stats() if stat.name == chosen_stat_name)

            dice_roll = roll_dice()
            success_threshold = 5  
            if chosen_stat.name == self.character.primary_stat:
                print(f"{self.character.name} is using their primary stat: {chosen_stat.name}")
                success_threshold -= 1
            if chosen_stat.value >= 10:
                success_threshold -= 1

            print(f"Dice roll: {dice_roll}")
            print(f"Attempting to fight {opponent_name} with {chosen_stat.name}...")

            if dice_roll >= success_threshold:
                print(f"{self.character.name} successfully attacked {opponent_name}!")
                player_score += 1
            else:
                print(f"{opponent_name} defended successfully!")
                opponent_score += 1

            if player_score == rounds:
                print(f"Congratulations! You have defeated {opponent_name}!")
            elif opponent_score == rounds:
                print(f"{opponent_name} has defeated you... Game Over.")
                self.continue_playing = False
                break

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
    regular_events = []
    battle_events = {"Draco": [], "Snape": [], "Voldemort": []}

    for event_data in data:
        event = Event(event_data)
        if event_data.get("is_battle_event", False):
            opponent = event_data.get("battle_event_for")
            if opponent and opponent in battle_events:
                battle_events[opponent].append(event)
        else:
            regular_events.append(event)
    return regular_events, battle_events

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
        character_choice = parser.parse("Enter the number or name of the character you want to play as: ").strip().lower()

        if character_choice in character_names:
            chosen_character = next(character for character in characters if character.name.lower() == character_names[character_choice].lower())
            break  # Exit the loop after a valid choice
        # Check if the input is a valid character name
        elif character_choice in (name.lower() for name in character_names.values()):
            chosen_character = next(character for character in characters if character.name.lower() == character_choice)
            break  # Exit the loop after a valid choice
        else:
            print("Invalid input. Please enter either the number or name of a character (Harry Potter, Hermione Granger, Ron Weasley).")

    print(f"You have chosen: {chosen_character.name}")

    regular_events, battle_events = load_events_from_json('project_code/location_events/location_2.json')
    locations = [Location(regular_events)]
    game = Game(parser, chosen_character, locations, battle_events)
    game.start()

if __name__ == '__main__':
    start_game()
