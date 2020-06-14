int f(){
    int a, b, c, d;
    if(a == a){ // 0
        a = 1;
        if (b == a){ // 1
            b = 3;
        }
        a = 2;
        if (b == c){ // 2
            c = 3;
        }
        else{ // 2
            if (c < 10){ // 3
                a = 10;
                if(a == 20){ // 4
                    print(a);
                }
                else{ // 4
                    print(b);
                } // 4
            } // 3
        } // 2
    }
    else if (b==0){
        b = 1;
    } // 1
    return c;
}
