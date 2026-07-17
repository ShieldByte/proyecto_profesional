public abstract class Animal {
    private String nombre;
    protected int edad;

    public Animal(String n, int e) {
        nombre = n;
        edad = e;
    }

    public abstract void hacerSonido();

    public String getNombre() {
        return nombre;
    }
}

public class Perro extends Animal implements Comparable {

    public Perro(String n, int e) {
        nombre = n;
        edad = e;
    }

    public void hacerSonido() {
        int contador = 0;
        while (contador < 3) {
            contador = contador + 1;
        }
    }

    public void hacerSonido(int veces) {
        int c = 0;
        for (int i = 0; i < veces; i++) {
            c = c + 1;
        }
    }

    public int comparar(int otro) {
        try {
            return otro / 2;
        } catch (Exception e) {
            throw e;
        } finally {
            return 0;
        }
    }
}
