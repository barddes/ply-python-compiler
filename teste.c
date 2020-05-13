int main () {
    int v[4] = {1, 2, 3};     // Error (size mismatch on initialization)
    float f;
    int j = v[f];             // Error (array index must be of type int)

    int a;
    float c;
    float b = a + c;

    j = f;                    // Error (canot assign float to int)

}