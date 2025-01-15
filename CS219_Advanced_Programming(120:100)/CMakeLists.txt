cmake_minimum_required(VERSION 3.10)

# 定义项目名称
project(MiniVim)

# 设置 C++ 标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 尝试自动查找 ncurses
find_package(Curses REQUIRED)

# 打印调试信息，确保路径正确
message(STATUS "CURSES_INCLUDE_DIR: ${CURSES_INCLUDE_DIR}")
message(STATUS "CURSES_LIBRARIES: ${CURSES_LIBRARIES}")

# 添加头文件路径
include_directories(${CURSES_INCLUDE_DIR})
include_directories(include)

# 定义源文件
set(SOURCES
    src/MiniVim.cpp
    main.cpp
)

# 定义可执行文件
add_executable(${PROJECT_NAME} ${SOURCES})

# 链接 ncurses 库
target_link_libraries(${PROJECT_NAME} ${CURSES_LIBRARIES})