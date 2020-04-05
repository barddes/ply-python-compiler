//
//int main () {
//    int v[] = {1, 2, 3, 4, 5};
//    int k = 3;
//    int p = v[k];
//    assert p == 4;
//    return;
//}

// Example 2:

int main () {
    float f = 1.0;
    char s[] = "xpto";
    print("este é um teste:", s);
    print(f);
    return 0;
}

// Example 3:
//
//int n = 3;
//
//int doubleMe (int x) {
//    return x * x;
//}
//
//void main () {
//    int v = n;
//    v = doubleMe (v);
//    assert v == n * n;
//    return 0;
//}
//
//// Example 4:
//
//int main () {
//    int i, j;
//    i = 1;
//    j = 2;
//    for (int k=1; k<10; k++)
//        i += j * k;
//    assert i == 91;
//    return 0;
//}
//
//// Example 5:
//// Não funciona p/ quem não implementar ponteiros em uC
//
//int main() {
//    int var[] = {100, 200, 300};
//    int *ptr;
//    ptr = var;
//    for(int i = 0; i < MAX; i++) {
//        assert var[i] == *ptr;
//        ptr++;
//    }
//    return 0;
//}
//
//// Example 6:
//
//int main() {
//    int h, b;
//    float area;
//    read(h);
//    read(b);
//    /*
//        Formula for the area of the triangle = (height x base)/2
//        Also, typecasting denominator from int to float
//    */
//    area = (h*b)/(float)2;
//    print("The area of the triangle is: ", area);
//    return 0;
//}