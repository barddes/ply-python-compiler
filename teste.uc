int checkPrime(int n) {
    int i, isPrime = 1;
    for (i = 2; i <= n/2; ++i) {
        if (n % i == 0) {
            isPrime = 0;
            break;
        }
        else{
            int a=1, b=2, c, d;
            a = c;
            b = d;
            if(c < d){
                print(a);
            }

            if(c<d && c > d){
                print(a);
            }

            if(!(c==d)){
                print("str");
            }

        }
    }
    i = 0;
    return isPrime;
}