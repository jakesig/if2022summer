# if2022summer

**Author:** Jake Sigman  
**Email:** <jsigman04@gmail.com>  
**Program:** Invention Factory  
**School:** The Cooper Union for the Advancement of Science and Art  
**Participated:** Summer 2022 


### Description

Code for Invention Factory in Summer of 2022. This repository uses AWS SQS to implement an Alexa skill, including all server-side and client-side code.

#### Directory Information **`ask-skill/`**

**`.ask/`**: Contains the Amazon Skill Kit library for VSCode    
**`lambda/`**: Contains lambda function for skill deployment    
**`skill-package/`**: Contains interaction and response models for the skill    
**`ask-resources.json`**: Contains skill information    

#### Directory Information **`client/`**
**`.esphome/`**: Contains the ESPHome library for interacting with the ESP8266    
**`main.py`**: Contains client-side code for receiving requests from SQS    
**`presets.txt`**: Contains stored presets set by user within the skill    
**`sinkmate.yaml`**: Configuration file for connecting the ESP8266 to the client  