# Arduino Stimulation Simulator
This module simulates the action of a stimulation unit by modifying a GPIO of an ardiuno,
which needs to be prepared to read from its serial connection.

The module will watch an LSL stream as defined in `./configs/arduino_stim_sim_config.toml`

## Code on the Arduino
This could be an example of the code flashed to the Arduino

```c 
const int inBufferSize = 32;
char inBuffer[inBufferSize];
int intFromSerial;
boolean newData = false;

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  
  Serial.begin(9600);
  Serial.println("Serial started!");

  // Use pin 2 for our signal
  pinMode(2, OUTPUT);

}

//============

void loop() {
    recvUntilNewLine();

    if (newData == true) { 
        intFromSerial = parseData(); 

        if (intFromSerial > 128 ) {
          Serial.println("Setting to high");
          digitalWrite(2, HIGH);
        }
        if (intFromSerial <= 128 ){
          Serial.println("Setting to low");
          digitalWrite(2, LOW);
        }
        // showParsedData();
        newData = false;
    }
}

//============

void recvUntilNewLine() {
    static byte ndx = 0;
    char endMarker = '\n';
    char rc;

    while (Serial.available() > 0 && newData == false) {
        rc = Serial.read();
          if (rc != endMarker) {
              inBuffer[ndx] = rc;
              ndx++;
              // in case of overflow
              if (ndx >= inBufferSize) {
                  ndx = inBufferSize - 1;
              }
          }
          else {
              inBuffer[ndx] = '\0'; // terminate the string
              ndx = 0;
              newData = true;
          }
    }
}

//============

// Read inBuffer to integer
int parseData() {
  int result = atoi(inBuffer);
  return result;
}

//============
void showParsedData() {
  Serial.print("inBuffer : {");
  for (int i=0; i < strlen(inBuffer) / sizeof(inBuffer[0]); i++){
    Serial.print(inBuffer[i]);
    Serial.print(", ");
  }
  Serial.println("}");

  Serial.print("Integer ");
  Serial.println(intFromSerial);

}
``` 
