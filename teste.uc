
int main () {
    int x, y;
    x = 1;
    y = 1;
    print(x);
    if (y > 1) {
        x = 2;
        if(x==0) {
            x =3;
        } else {
            x = 4;
        }
        x = 5;
    }
    print(x);
    return 0;
}