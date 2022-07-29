// Pin definitions

#define SENSOR A0
#define VALVE 1

// Setup block

void setup() {
  
  // Declare pin modes
  
  pinMode(SENSOR, INPUT);
  pinMode(VALVE, OUTPUT);

  // Begin serial output
  
  Serial.begin(115200);
}

// Loop block

void loop () {

  // Log value from flow sensor
  
  Serial.println(float(analogRead(SENSOR)));

  // Write values to valve
  
  digitalWrite(VALVE, HIGH);
  delay(1000);
  digitalWrite(VALVE, LOW);
  delay(1000);
}
