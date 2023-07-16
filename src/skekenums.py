from enum import Enum

class AI_Personality(Enum):
    Balanced = 10
    Drunk = 11
    Snarky = 12
    Serious = 13
    Stupid = 14
    Creative = 15
    Sentient = 16
    Philosophical = 17
    Military = 18

    def __str__(self):
        return self.name

class AI_API(Enum):
    Image = "DALL-E 2"
    Variation = "Variations"
    Chat = "gpt-3.5-turbo"

    def __str__(self):
        return self.value
    

class Resolution(Enum):
    Low = "256x256"
    Med = "512x512"
    High = "1024x1024"

    def __str__(self):
        return self.value
    
class ImageMode(Enum):
    Generation = 1
    Variation = 2

    def __str__(self):
        return self.name
    
class SpeechModel(Enum):
    Adam = "Adam"
    Antoni = "Antoni"
    Arnold = "Arnold"
    Josh = "Josh"
    Sam = "Sam"
    Bella = "Bella"
    Domi = "Domi"
    Elli = "Elli"
    Rachel = "Rachel"

    def __str__(self):
        return self.value
    

class ChatFilter(Enum):
    "Enums 30-40."
    Pigeon = 30,