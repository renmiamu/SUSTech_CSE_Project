#include "MiniVim.h"

int main() {
    std:: string filename;
    std:: cin >> filename;
    MiniVim editor = MiniVim(filename);
    editor.run();
    return 0;
}
