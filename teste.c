//apenas foo() nao eh salva em environment
int foo()  {
    return 0;
}

int b = 2;

int main () {
    int a = foo();
    a = b;
    return 0;
}