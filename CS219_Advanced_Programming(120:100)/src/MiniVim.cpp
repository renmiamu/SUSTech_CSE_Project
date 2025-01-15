  #include "MiniVim.h"
MiniVim::MiniVim(const std::string &filename) {
    initscr();
    raw();
    keypad(stdscr, TRUE);
    noecho();
    curs_set(1);
    init_colors();

    // 检查文件路径，避免重复前缀
    if (filename.find("../files/") == 0) {
        file_name = filename + ".txt";
    } else {
        file_name = "../files/" + filename + ".txt";
    }

    // 打开文件或创建新文件
    std::ifstream new_file(file_name);

    if (!new_file.is_open()) {
        std::ofstream create_file(file_name);
        if (!create_file.is_open()) {
            display_message("cannot create file: " + file_name);
            return;
        }
        // 默认内容为文件的绝对路径
        create_file << file_name << "\n";
        create_file.close();
        display_message("file doesn't exist, new file created: " + file_name);
    } else {
        if (new_file.peek() == EOF) {
            new_file.close(); 

            std::ofstream out_file(file_name, std::ios::out);
            if (out_file.is_open()) {
                out_file << " ";
                out_file.close();
            }
        } else {
            display_message("entered " + file_name);
        }
    }

    new_file.close();
     // 初始化文件上下文
    FileContext context;
    load_file_into_context(context, current_file);
    file_contexts[current_file] = context;

    // 恢复当前文件上下文
    restore_file_context(file_contexts[current_file]);

    load_file();

    view_start_x = 0;
    view_start_y = 0;
    screen_width = COLS - get_line_number_width() - 2;
    screen_height = LINES - 1;
}


  MiniVim::~MiniVim() {
      endwin();
  }

void MiniVim::run() {
    int ch;
    while (true) {
        int new_screen_height = LINES - 1; // LINES 表示终端的当前行数
        int new_screen_width = COLS - get_line_number_width() - 2; // COLS 表示终端的当前列数

        if (new_screen_height != screen_height || new_screen_width != screen_width) {
            // 更新屏幕尺寸
            screen_height = new_screen_height;
            screen_width = new_screen_width;

            // 防止视图范围超出文件内容
            if (y >= view_start_y + screen_height) {
                view_start_y = y - screen_height + 1;
            }
            if (x >= view_start_x + screen_width) {
                view_start_x = x - screen_width + 1;
            }
            if (view_start_y + screen_height > text.size()) {
                view_start_y = text.size() - screen_height;
            }
            if (view_start_y < 0) {
                view_start_y = 0;
            }

            clear(); // 清屏
        }
        display_text_with_line_numbers();
        display_mode();
        move(y - view_start_y, x - view_start_x + get_line_number_width() + 1);
        refresh();

        ch = getch();
        int next_ch;
        switch (ch) {
            case 'i':
                mode = "--INSERT--";
                display_mode();
                insert_mode();
                mode = "--NORMAL--";
                break;

            case ':':
                display_mode(false);
                command_mode();
                break;

            case 'h':
                move_cursor(-1, 0);
                break;

            case 'j':
                move_cursor(0, 1);
                break;

            case 'k':
                move_cursor(0, -1);
                break;

            case 'l':
                move_cursor(1, 0);
                if (x >= view_start_x + screen_width - 1) {
                    view_start_x++;
                }
                break;

            case 'u':
                undo();
                break;

            case 18: 
                redo();
                break;

            case KEY_LEFT:
                move_cursor(-1, 0);
                break;

            case KEY_RIGHT:
                move_cursor(1, 0);
                if (x >= view_start_x + screen_width - 1) {
                    view_start_x++;
                }
                break;

            case KEY_UP:
                move_cursor(0, -1);
                break;

            case KEY_DOWN:
                move_cursor(0, 1);
                break;

            case '0':
                x = 0;
                break;

            case '$':
                x = text[y].length(); // 移动到行尾
    if (x >= view_start_x + screen_width) {
        view_start_x = x - (screen_width - 1); // 调整水平滚动范围
    }
    if (x < view_start_x) {
        view_start_x = x; // 如果光标在屏幕左边界外，也需要调整水平滚动范围
    }
                break;

            case 'g':
                if (getch() == 'g') {
                    y = 0;
                    x = 0;
                    view_start_y = 0; // 滚动视图到顶部
                }
                break;

            case 'G':
                y = text.size() - 1; // 跳转到最后一行
                x = 0; // 光标移动到行首
                break;

            case 'd':
                next_ch = getch();
                if (next_ch == 'd') {
                    delete_line();
                } else {
                    ungetch(next_ch);
                }
                break;

            case 'y':
                next_ch = getch();
                if (next_ch == 'y') {
                    if (!text.empty() && y < text.size()) {
                        copied_line = text[y];
                    }
                } else {
                    ungetch(next_ch);
                }
                break;

            case 'p':
                if (!copied_line.empty()) {
                    save_state_to_undo();
                    text.insert(text.begin() + y + 1, copied_line);
                    y++;
                }
                break;

            case 2: // Ctrl + B (加粗模式)
                set_font_style(A_BOLD);
                break;

            case 21: // Ctrl + U (下划线模式)
                set_font_style(A_UNDERLINE);
                break;

            case 14: // Ctrl + N (正常模式)
                set_font_style(A_NORMAL);
                break;    

            default:
                break;
        }

        // 确保光标在视图范围内
        if (y < view_start_y) {
            view_start_y = y; // 光标在视图上方时，调整视图顶部
        } else if (y >= view_start_y + screen_height) {
            view_start_y = y - (screen_height - 1); // 光标在视图下方时，滚动视图
        }

        // 确保视图范围不会超出文件内容
        if (view_start_y + screen_height > text.size()) {
            view_start_y = text.size() - screen_height; // 限制视图滚动范围
        }
        if (view_start_y < 0) {
            view_start_y = 0; // 防止视图起始位置为负数
        }

        clear();
        display_text_with_line_numbers();
        display_mode();
        if (x < 0) x = 0;
    if (y < 0) y = 0;
    if (y >= text.size()) y = text.size() - 1;
    if (x > text[y].length()) x = text[y].length();

    if (y < view_start_y) {
        view_start_y = y;
    } else if (y >= view_start_y + screen_height - 1) {
        view_start_y = y - (screen_height - 2);
    }

    if (x < view_start_x) {
        view_start_x = x;
    } else if (x >= view_start_x + screen_width - 1) {
        view_start_x = x - (screen_width - 1);
    }

    move(y - view_start_y, x - view_start_x + get_line_number_width() + 1);
    refresh();
        refresh();
    }
}

  void MiniVim::delete_line() {
    if (!text.empty() && y < text.size()) {
        if (get_line_number_width()-1 != text[y].length())
        {
            save_state_to_undo(); 
        }
        if (y == 0 && text.size() == 1) {
            text[y].erase(get_line_number_width() - 1, text[y].length());
        }
        else {
            text.erase(text.begin() + y);
                y--;
                if (y < 0) {
                    y = 0;
                }
            }
        x = 0;
    }
  }

void MiniVim::init_colors() {
    if (has_colors()) {
        start_color();
        init_pair(1, COLOR_WHITE, COLOR_BLACK);   // 默认颜色（白色文字，黑色背景）
        init_pair(2, COLOR_BLACK, COLOR_WHITE);   // 反转颜色（黑色文字，白色背景）
        init_pair(3, COLOR_GREEN, COLOR_BLACK);   // 插入模式绿色
        init_pair(4, COLOR_BLUE, COLOR_BLACK);    // 命令模式蓝色
        init_pair(5, COLOR_RED, COLOR_BLACK);     // 错误信息红色
        init_pair(6, COLOR_YELLOW, COLOR_BLACK);  // 高亮当前行黄色字体，黑色背景
        init_pair(7, COLOR_BLACK, COLOR_YELLOW);  // 高亮当前行黑色字体，黄色背景（白色模式下）
        init_pair(8, COLOR_BLUE, COLOR_WHITE);    // 模式行深蓝色字体，白色背景（白色模式下）
        init_pair(9, COLOR_RED, COLOR_WHITE);
    }
}

  void MiniVim::load_file() {
      std::ifstream file(file_name);
      if (file.is_open()) {
          std::string line;
          while (getline(file, line)) {
              text.push_back(line);
          }
          file.close();
      }
      // 如果文件内容为空，添加一个空格以确保正常显示
    if (text.empty()) {
        text.push_back(" "); // 添加一行空格
    }
  }

void MiniVim::insert_mode() {
    int ch;
    move(y - view_start_y, x - view_start_x + get_line_number_width() + 1);

    while (true) {
        ch = getch();
        if (ch == 27) {
            if (y >= view_start_y + screen_height - 1) {
                view_start_y++;
                y = view_start_y + screen_height - 2;
            }
            return;
        }

        save_state_to_undo();

        if (ch == KEY_BACKSPACE || ch == 127) {
            if (x > 0) {
                text[y].erase(x - 1, 1);
                x--;
            } else if (y > 0) {
                x = text[y - 1].length();
                text[y - 1] += text[y];
                text.erase(text.begin() + y);
                y--;
            }
        } else if (ch == '\n') {
    // 将光标后面的内容移动到新行
    text.insert(text.begin() + y + 1, text[y].substr(x));
    text[y] = text[y].substr(0, x);

    // 光标移动到新行的行首
    y++;
    x = 0; // 重置列到行首
    view_start_x = 0; // 重置水平视图起始位置

    // 如果超出屏幕高度，更新视图
    if (y >= view_start_y + screen_height - 1) {
        view_start_y++;
    }
} else if (ch == KEY_LEFT) {
            move_cursor(-1, 0);
        } else if (ch == KEY_RIGHT) {
            move_cursor(1, 0);
        } else if (ch == KEY_UP) {
            move_cursor(0, -1);
        } else if (ch == KEY_DOWN) {
            move_cursor(0, 1);
        } else { 
            text[y].insert(x, 1, ch);
            x++;

            if (x >= view_start_x + screen_width - 1) {
                view_start_x++;
            }
        }

        clear();
        display_text_with_line_numbers();
        display_mode();
        if (x < 0) x = 0;
    if (y < 0) y = 0;
    if (y >= text.size()) y = text.size() - 1;
    if (x > text[y].length()) x = text[y].length();

    if (y < view_start_y) {
        view_start_y = y;
    } else if (y >= view_start_y + screen_height - 1) {
        view_start_y = y - (screen_height - 2);
    }

    if (x < view_start_x) {
        view_start_x = x;
    } else if (x >= view_start_x + screen_width - 1) {
        view_start_x = x - (screen_width - 1);
    }

    move(y - view_start_y, x - view_start_x + get_line_number_width() + 1);
    refresh();
        refresh();
    }
}

  void MiniVim::command_mode() {
      int max_y, max_x;
      getmaxyx(stdscr, max_y, max_x);
      int command_line = max_y - 1;
      command_str = "";
      move(command_line, 0);
      mvprintw(command_line, 0, ":");
      refresh();

      while (true) {
          int ch = getch();
          if (ch == 27) {
              clear();
              return;
          }
          if (ch == KEY_BACKSPACE || ch == 127) {
              if (!command_str.empty()) {
                  command_str.pop_back();
                  move(command_line, 1 + command_str.length());
                  delch();
              }
          } else if (ch != '\n') {
              command_str.push_back(ch);
              addch(ch);
          } else if (ch == '\n') {
              noecho();
              process_command();
              clear();
              return;
          }
          refresh();
      }
  }

  void MiniVim::process_command() {
    if (command_str == "w") {
        save_file(current_file);
    } else if (command_str == "q") {
        save_current_file_context();
        endwin();
        exit(0);
    } else if (command_str == "wq") {
        save_file(current_file);
        endwin();
        exit(0);
    } else if (command_str == "background") {
        toggle_background();
    } else if (command_str.rfind("s/", 0) == 0) {
        handle_find_and_replace();
    }else if (is_number(command_str)) {
    int line_number = std::stoi(command_str);
    if (line_number >= 1 && line_number <= text.size()) {
    y = line_number - 1; // 设置光标到指定行
    x = 0;               // 重置列到行首

    if (y < view_start_y) {
        view_start_y = y;
    } else if (y >= view_start_y + screen_height - 1) {
        view_start_y = y - (screen_height - 2);
        if (view_start_y < 0) {
            view_start_y = 0;
        }
    }

    clear();
    display_text_with_line_numbers();
    display_mode();
    refresh();
}

     else {
        display_message("line number exceeded.");
    }
} else if (command_str.rfind("cd/", 0) == 0) {
    save_current_file_context();
        std::string filename = command_str.substr(3);
        change_file(filename);
    } else {
        display_message("unknown command: " + command_str);
    }
}

void MiniVim::handle_find_and_replace() {
    save_state_to_undo();
    size_t first_slash = command_str.find('/', 0);
size_t second_slash = command_str.find('/', first_slash + 1);
size_t third_slash = command_str.find('/', second_slash + 1);

// 检查命令格式是否正确
if (first_slash == std::string::npos || second_slash == std::string::npos) {
    display_message("command format invalid, please use: s/old/new or s/old/new/g");
    return;
}

std::string old_str = command_str.substr(first_slash + 1, second_slash - first_slash - 1);
std::string new_str;

if (third_slash != std::string::npos) {
    // 如果有第三个斜杠，说明命令格式是 s/old/new/g
    new_str = command_str.substr(second_slash + 1, third_slash - second_slash - 1);
} else {
    // 如果没有第三个斜杠，说明命令格式是 s/old/new
    new_str = command_str.substr(second_slash + 1);
}


    // 判断是否全局替换
    bool global_replace = (third_slash != std::string::npos && command_str.substr(third_slash) == "/g");

    // 如果替换的字符串为空
    if (old_str.empty()) {
        display_message("old string cannot be empty");
        return;
    }

    int replace_count = 0;

    if (global_replace) {
        // 替换文件中所有行的所有匹配
        for (std::string &line : text) {
            size_t pos = 0;
            while ((pos = line.find(old_str, pos)) != std::string::npos) {
                line.replace(pos, old_str.length(), new_str);
                pos += new_str.length(); // 继续查找替换后的字符串之后的位置
                replace_count++;
            }
        }
    } else {
        // 只替换当前行的第一个匹配
        if (y < text.size()) {
            size_t pos = text[y].find(old_str);
            if (pos != std::string::npos) {
                text[y].replace(pos, old_str.length(), new_str);
                replace_count++;
            }
        }
    }

    // 显示替换结果
    if (replace_count > 0) {
        display_message("successfully replaced, total replaced in " + std::to_string(replace_count) + " places.");
    } else {
        display_message("cannot find old string.");
    }
}

  void MiniVim::save_file(const std::string &filename) {
      std::ofstream file(filename);
      if (file.is_open()) {
          for (const auto &line : text) {
              file << line << std::endl;
          }
          file.close();
      }
  }

void MiniVim::move_cursor(int dx, int dy) {
    x += dx;
    y += dy;

    if (x < 0) x = 0;
    if (y < 0) y = 0;
    if (y >= text.size()) y = text.size() - 1;
    if (x > text[y].length()) x = text[y].length();

    if (y < view_start_y) {
        view_start_y = y;
    } else if (y >= view_start_y + screen_height - 1) {
        view_start_y = y - (screen_height - 2);
    }

    if (x < view_start_x) {
        view_start_x = x;
    } else if (x >= view_start_x + screen_width - 1) {
        view_start_x = x - (screen_width - 1);
    }

    move(y - view_start_y, x - view_start_x + get_line_number_width() + 1);
    refresh();
}

  void MiniVim::display_mode(bool show) {
    int max_y, max_x;
    getmaxyx(stdscr, max_y, max_x);
    move(max_y - 1, 0); // 移动到模式行位置
    clrtoeol();         // 清空当前行

    if (show) {
        if (is_default_background) {
            // 黑色背景模式
            attron(COLOR_PAIR(3)); // 绿色字体，黑色背景
        } else {
            // 白色背景模式
            attron(COLOR_PAIR(8)); // 深蓝色字体，白色背景
        }

        mvprintw(max_y - 1, 0, "%s", mode.c_str()); // 打印模式字符串

        if (is_default_background) {
            attroff(COLOR_PAIR(3));
        } else {
            attroff(COLOR_PAIR(8));
        }
    }

    refresh();
}

  int MiniVim::get_line_number_width() {
      int num_lines = text.size();
      int width = 1;
      while (num_lines >= 10) {
          num_lines /= 10;
          width++;
      }
      return width;
  }

void MiniVim::display_text_with_line_numbers() {
    int line_number_width = get_line_number_width();

    for (int i = 0; i < screen_height - 1; ++i) {
        int text_line = i + view_start_y;
        if (text_line >= text.size()) break;

        std::string line = text[text_line];
        if (view_start_x < line.length()) {
            line = line.substr(view_start_x, screen_width);
        } else {
            line = "";
        }

        // 渲染行号（仅颜色跟内容一致，不受字体样式影响）
        if (is_default_background) {
            attron(COLOR_PAIR(1)); // 黑色背景：白色文字
        } else {
            attron(COLOR_PAIR(2)); // 白色背景：黑色文字
        }
        mvprintw(i, 0, "%*d ", line_number_width, text_line + 1); // 显示行号
        if (is_default_background) {
            attroff(COLOR_PAIR(1));
        } else {
            attroff(COLOR_PAIR(2));
        }

        // 渲染行内容
        if (text_line == y) { // 当前行
            if (is_default_background) {
                attron(COLOR_PAIR(6) | current_font_style); // 黑色背景：黄色文字 + 字体样式
            } else {
                attron(COLOR_PAIR(7) | current_font_style); // 白色背景：黄色背景，黑色文字 + 字体样式
            }
            mvprintw(i, line_number_width + 1, "%s", line.c_str());
            if (is_default_background) {
                attroff(COLOR_PAIR(6) | current_font_style);
            } else {
                attroff(COLOR_PAIR(7) | current_font_style);
            }
        } else { // 普通行
            if (is_default_background) {
                attron(COLOR_PAIR(1) | current_font_style); // 黑色背景：白色文字 + 字体样式
            } else {
                attron(COLOR_PAIR(2) | current_font_style); // 白色背景：黑色文字 + 字体样式
            }
            mvprintw(i, line_number_width + 1, "%s", line.c_str());
            if (is_default_background) {
                attroff(COLOR_PAIR(1) | current_font_style);
            } else {
                attroff(COLOR_PAIR(2) | current_font_style);
            }
        }
    }

    display_mode(); // 渲染模式行
}

  void MiniVim::save_state_to_undo() {
      //保存当前文本和光标位置到撤销栈
      undo_stack.push({text, {x, y}});
      // 清空重做栈
      while (!redo_stack.empty()) {
          redo_stack.pop();
      }
  }

  void MiniVim::undo() {
      if (!undo_stack.empty()) {
          // 保存当前状态到重做栈
          redo_stack.push({text, {x, y}});
          // 恢复撤销栈状态
          text = undo_stack.top().first;
          x = undo_stack.top().second.first;
          y = undo_stack.top().second.second;
          undo_stack.pop();
          refresh();
      }
  }

  void MiniVim::redo() {
      if (!redo_stack.empty()) {
          // 保存当前状态到撤销栈
          undo_stack.push({text, {x, y}});
          // 恢复重做栈状态
          text = redo_stack.top().first;
          x = redo_stack.top().second.first;
          y = redo_stack.top().second.second;
          redo_stack.pop();
          refresh();
      }
  }

  bool MiniVim::is_number(const std::string &str) {
      if (str.empty()) return false;  // 空字符串不是数字

      for (char ch : str) {
          if (!std::isdigit(ch)) {
              return false;  // 如果有任何非数字字符，返回 false
          }
      }
      return true;
  }

  void MiniVim::display_message(const std::string &message) {
    int max_y, max_x;
    getmaxyx(stdscr, max_y, max_x);
    move(max_y - 2, 0); // 移动到消息行位置
    clrtoeol();         // 清空当前行

    if (is_default_background) {
        attron(COLOR_PAIR(5));
    } else {
        attron(COLOR_PAIR(9));
    }

    mvprintw(max_y - 2, 0, "%s", message.c_str());

    if (is_default_background) {
        attroff(COLOR_PAIR(5));
    } else {
        attroff(COLOR_PAIR(9));
    }

    refresh();
    napms(1000);
    clear();
}

void MiniVim::toggle_background() {
    is_default_background = !is_default_background; // 切换背景状态

    // 设置全局背景颜色
    if (is_default_background) {
        bkgd(COLOR_PAIR(1)); // 黑色背景，白色文字
        display_message("Switched to BLACK background");
    } else {
        bkgd(COLOR_PAIR(2)); // 白色背景，黑色文字
        display_message("Switched to WHITE background");
    }

    // 清屏并重新渲染所有内容
    clear();
    display_text_with_line_numbers();
    display_mode();
    refresh();
}

void MiniVim::change_file(const std::string &filename) {
    // 保存当前文件的上下文
    save_current_file_context();

    // 更新当前文件路径
    std::string new_file = "../files/" + filename + ".txt";
    current_file = new_file;

    // 如果文件已存在于 file_contexts，则恢复其上下文
    if (file_contexts.find(current_file) != file_contexts.end()) {
        restore_file_context(file_contexts[current_file]);
    } else {
        // 如果是新文件，加载其内容到新上下文
        FileContext new_context;
        load_file_into_context(new_context, current_file);
        file_contexts[current_file] = new_context;

        // 将新文件的上下文设置为当前编辑状态
        restore_file_context(new_context);
    }

    // 更新屏幕
    clear();
    display_text_with_line_numbers();
    display_mode();
    refresh();
}

void MiniVim::save_current_file_context() {
    FileContext &context = file_contexts[current_file];
    context.text = text;
    context.x = x;
    context.y = y;
    context.view_start_x = view_start_x;
    context.view_start_y = view_start_y;
    context.undo_stack = undo_stack;
    context.redo_stack = redo_stack;
}

void MiniVim::restore_file_context(const FileContext &context) {
    text = context.text;
    x = context.x;
    y = context.y;
    view_start_x = context.view_start_x;
    view_start_y = context.view_start_y;
    undo_stack = context.undo_stack;
    redo_stack = context.redo_stack;
}

void MiniVim::load_file_into_context(FileContext &context, const std::string &filename) {
    std::ifstream file(filename);

    if (file.is_open()) {
        std::string line;
        while (getline(file, line)) {
            context.text.push_back(line);
        }
        file.close();
    }

    if (context.text.empty()) {
        context.text.push_back(" "); // 如果文件为空，插入一个空格
    }

    context.x = 0;
    context.y = 0;
    context.view_start_x = 0;
    context.view_start_y = 0;
}

void MiniVim::set_font_style(int style) {
    current_font_style = style;

    // 提示用户当前字体样式
    if (style == A_BOLD) {
        display_message("Font style: Bold");
    } else if (style == A_UNDERLINE) {
        display_message("Font style: Underline");
    } else if (style == A_NORMAL) {
        display_message("Font style: Normal");
    }

    // 重新渲染界面以应用新的字体样式
    clear();
    display_text_with_line_numbers();
    display_mode();
    refresh();
}
