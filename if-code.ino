void setup() {
   pinMode(A0, INPUT);
   pinMode(1, OUTPUT);
   Serial.begin(115200);
}

void loop () {
  Serial.println(float(analogRead(A0)));
  digitalWrite(1, HIGH);
  delay(1000);
  digitalWrite(1, LOW);
  delay(1000);
}
