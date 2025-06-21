# CS307_Principles_of_Database_System_Project2

## Task3: Optimizer（Index Optimization）

### 2.Advanced:  Index Optimization Implementation

1. #### Index Support:

项目实现了两种索引机制，分别为原有的InMemoryOrderedIndex和advance部分要求的B+树索引。

大致功能如下：

#### create index:

创建索引，要求无重复元素。如果出现重复值会报错：Duplicated index.

会自动创建B+树索引。（可以在Logical Planner中切换）

SQL:

```sql
create index index_name on student(name);
```

执行该SQL后程序会在 `CS307-DB/meta` 目录下创建该index对应的 `tableName_columnName_IndexType.json` 文件，用于持久化在硬盘上存储索引信息，格式大致如下。

```json
{
  "char_Alice": {
    "pageNum": 1,
    "slotNum": 0
  },
  "char_Amy": {
    "pageNum": 1,
    "slotNum": 26
  },
  "char_Bob": {
    "pageNum": 1,
    "slotNum": 1
  },
 ... 
}  
```

重启数据库后，如果查询可以通过B+树索引执行，程序可以直接从对应的json文件中读取index信息进行查询。

应该实现了**Persistent Storage:**

- Store index structures on disk 
- Ensure index persistence after system restart

#### drop index:

删除先前创建的索引

SQL:

```sql
drop index name on student;
```

#### 基于索引范围查找

可以根据SQL简单生成相应的查询逻辑，可以在filter层出现**Binary Expression** 或 **Between Expression** 的时候生成基于索引的查询逻辑。（Between查询左闭右开）

如果使用B+树索引查询，会打印B+树（直接调用toString方法）

SQL:

```sql
select id, name from student where name = 'Sam';
select * from student where id between 20 and 40;
```

#### 多索引支持

同一表能建多个索引文件，允许**按列建多个索引**， 能自动区分不同 `col` 对应哪个索引

SQL与先前create index相同

```sql
create index index_id on student(id);
```

2. #### Validation

为了验证B+树索引的正确性以及效率，我使用 `StudentInfomationGenerator` 脚本向 CS307-DB中的`student` 表中插入了一万条数据。同时我在 `DataGrip` 中也插入了完全相同的数据。经过了漫长的等待之后进行测试：

1. 不使用index：

   在 `CS307-DB` 中，分别使用如下SQL指令：

   ```sql
   select id, name from student where name = 'Zach_user7671';
   ```

   ```sql
   select id, name from student where id between 9980 and 9999;
   ```

   得到输出：

   ```
   08:01:45.522 INFO: ┌───────────────┐───────────────┐
   08:01:45.526 INFO: |  student.id   | student.name  |
   08:01:45.527 INFO: +───────────────+───────────────+
   08:01:45.606 INFO: |     7671      | Zach_user7671 |
   08:01:45.606 INFO: +───────────────+───────────────+
   ```

   ```
   11:36:16.281 INFO: ┌───────────────┐───────────────┐
   11:36:16.284 INFO: |  student.id   | student.name  |
   11:36:16.284 INFO: +───────────────+───────────────+
   11:36:16.407 INFO: |     9980      |Kevin_user9980 |
   11:36:16.407 INFO: +───────────────+───────────────+
   11:36:16.407 INFO: |     9981      |Mallory_user9981|
   11:36:16.407 INFO: +───────────────+───────────────+
   11:36:16.407 INFO: |     9982      |Laura_user9982 |
   11:36:16.407 INFO: +───────────────+───────────────+
   11:36:16.408 INFO: |     9983      |Laura_user9983 |
   11:36:16.408 INFO: +───────────────+───────────────+
   11:36:16.408 INFO: |     9984      |Alice_user9984 |
   11:36:16.408 INFO: +───────────────+───────────────+
   11:36:16.408 INFO: |     9985      | Niaj_user9985 |
   11:36:16.408 INFO: +───────────────+───────────────+
   11:36:16.408 INFO: |     9986      | Uma_user9986  |
   11:36:16.408 INFO: +───────────────+───────────────+
   11:36:16.408 INFO: |     9987      |Kevin_user9987 |
   11:36:16.408 INFO: +───────────────+───────────────+
   11:36:16.408 INFO: |     9988      | Eve_user9988  |
   11:36:16.408 INFO: +───────────────+───────────────+
   11:36:16.408 INFO: |     9989      | Ivan_user9989 |
   11:36:16.408 INFO: +───────────────+───────────────+
   11:36:16.409 INFO: |     9990      |Sybil_user9990 |
   11:36:16.409 INFO: +───────────────+───────────────+
   11:36:16.409 INFO: |     9991      |Peggy_user9991 |
   11:36:16.409 INFO: +───────────────+───────────────+
   11:36:16.409 INFO: |     9992      | Eve_user9992  |
   11:36:16.409 INFO: +───────────────+───────────────+
   11:36:16.409 INFO: |     9993      |Wendy_user9993 |
   11:36:16.409 INFO: +───────────────+───────────────+
   11:36:16.409 INFO: |     9994      | Zach_user9994 |
   11:36:16.409 INFO: +───────────────+───────────────+
   11:36:16.409 INFO: |     9995      |Frank_user9995 |
   11:36:16.409 INFO: +───────────────+───────────────+
   11:36:16.409 INFO: |     9996      |Mallory_user9996|
   11:36:16.409 INFO: +───────────────+───────────────+
   11:36:16.409 INFO: |     9997      |Frank_user9997 |
   11:36:16.409 INFO: +───────────────+───────────────+
   11:36:16.409 INFO: |     9998      | Judy_user9998 |
   11:36:16.409 INFO: +───────────────+───────────────+
   ```

   总运行时长分别为： 84ms 和 128ms

   

   在 `DataGrip` 中，分别使用如下SQL指令：

   ```sql
   select id, name from student where name = 'Zach_user7671';
   ```

   ```sql
   select id, name from student where id between 9980 and 9999;
   ```

   得到输出：

   | id   | name          |
   | ---- | ------------- |
   | 7671 | Zach_user7671 |

   | id   | name             |
   | ---- | ---------------- |
   | 9980 | Kevin_user9980   |
   | 9981 | Mallory_user9981 |
   | 9982 | Laura_user9982   |
   | 9983 | Laura_user9983   |
   | 9984 | Alice_user9984   |
   | 9985 | Niaj_user9985    |
   | 9986 | Uma_user9986     |
   | 9987 | Kevin_user9987   |
   | 9988 | Eve_user9988     |
   | 9989 | Ivan_user9989    |
   | 9990 | Sybil_user9990   |
   | 9991 | Peggy_user9991   |
   | 9992 | Eve_user9992     |
   | 9993 | Wendy_user9993   |
   | 9994 | Zach_user9994    |
   | 9995 | Frank_user9995   |
   | 9996 | Mallory_user9996 |
   | 9997 | Frank_user9997   |
   | 9998 | Judy_user9998    |
   | 9999 | Grace_user9999   |


   总运行时长分别为： 307ms 和 254ms

   ```
1 row retrieved starting from 1 in 307 ms (execution: 4 ms, fetching: 303 ms)
   ```

   ```
20 rows retrieved starting from 1 in 254 ms (execution: 3 ms, fetching: 251 ms)
   ```

2. 使用index：

3. 在 `CS307-DB` 中，使用如下SQL指令：

   ```sql
   create index index_name on student(name);
   select id, name from student where name = 'Zach_user7671';
   ```

   得到输出：

   ```
   08:03:39.613 INFO: ┌───────────────┐───────────────┐
   08:03:39.613 INFO: |  student.id   | student.name  |
   08:03:39.613 INFO: +───────────────+───────────────+
   08:03:39.613 INFO: |     7671      | Zach_user7671 |
   08:03:39.613 INFO: +───────────────+───────────────+
   ```

   ```
   11:37:26.355 INFO: ┌───────────────┐───────────────┐
   11:37:26.355 INFO: |  student.id   | student.name  |
   11:37:26.355 INFO: +───────────────+───────────────+
   11:37:26.358 INFO: |     9980      |Kevin_user9980 |
   11:37:26.358 INFO: +───────────────+───────────────+
   11:37:26.358 INFO: |     9981      |Mallory_user9981|
   11:37:26.358 INFO: +───────────────+───────────────+
   11:37:26.358 INFO: |     9982      |Laura_user9982 |
   11:37:26.358 INFO: +───────────────+───────────────+
   11:37:26.358 INFO: |     9983      |Laura_user9983 |
   11:37:26.358 INFO: +───────────────+───────────────+
   11:37:26.358 INFO: |     9984      |Alice_user9984 |
   11:37:26.358 INFO: +───────────────+───────────────+
   11:37:26.358 INFO: |     9985      | Niaj_user9985 |
   11:37:26.358 INFO: +───────────────+───────────────+
   11:37:26.358 INFO: |     9986      | Uma_user9986  |
   11:37:26.358 INFO: +───────────────+───────────────+
   11:37:26.358 INFO: |     9987      |Kevin_user9987 |
   11:37:26.358 INFO: +───────────────+───────────────+
   11:37:26.358 INFO: |     9988      | Eve_user9988  |
   11:37:26.358 INFO: +───────────────+───────────────+
   11:37:26.358 INFO: |     9989      | Ivan_user9989 |
   11:37:26.358 INFO: +───────────────+───────────────+
   11:37:26.359 INFO: |     9990      |Sybil_user9990 |
   11:37:26.359 INFO: +───────────────+───────────────+
   11:37:26.359 INFO: |     9991      |Peggy_user9991 |
   11:37:26.359 INFO: +───────────────+───────────────+
   11:37:26.359 INFO: |     9992      | Eve_user9992  |
   11:37:26.359 INFO: +───────────────+───────────────+
   11:37:26.359 INFO: |     9993      |Wendy_user9993 |
   11:37:26.359 INFO: +───────────────+───────────────+
   11:37:26.359 INFO: |     9994      | Zach_user9994 |
   11:37:26.359 INFO: +───────────────+───────────────+
   11:37:26.359 INFO: |     9995      |Frank_user9995 |
   11:37:26.359 INFO: +───────────────+───────────────+
   11:37:26.359 INFO: |     9996      |Mallory_user9996|
   11:37:26.359 INFO: +───────────────+───────────────+
   11:37:26.359 INFO: |     9997      |Frank_user9997 |
   11:37:26.359 INFO: +───────────────+───────────────+
   11:37:26.359 INFO: |     9998      | Judy_user9998 |
   11:37:26.359 INFO: +───────────────+───────────────+
   ```

   总运行时长分别变为小于 1ms 和 大约 4ms

   

   在 `DataGrip` 中，分别使用如下SQL指令：

   ```sql
   create index index_name on student(name);
   select id, name from student where name = 'Zach_user7671';
   ```

   ```sql
   create index index_id on student(id);
   select id, name from student where id between 9980 and 9999;
   ```

   得到输出：

   | id   | name          |
   | ---- | ------------- |
   | 7671 | Zach_user7671 |

   | id   | name             |
   | ---- | ---------------- |
   | 9980 | Kevin_user9980   |
   | 9981 | Mallory_user9981 |
   | 9982 | Laura_user9982   |
   | 9983 | Laura_user9983   |
   | 9984 | Alice_user9984   |
   | 9985 | Niaj_user9985    |
   | 9986 | Uma_user9986     |
   | 9987 | Kevin_user9987   |
   | 9988 | Eve_user9988     |
   | 9989 | Ivan_user9989    |
   | 9990 | Sybil_user9990   |
   | 9991 | Peggy_user9991   |
   | 9992 | Eve_user9992     |
   | 9993 | Wendy_user9993   |
   | 9994 | Zach_user9994    |
   | 9995 | Frank_user9995   |
   | 9996 | Mallory_user9996 |
   | 9997 | Frank_user9997   |
   | 9998 | Judy_user9998    |
   | 9999 | Grace_user9999   |

   总运行时长为： 255ms 和 25ms

   ```
   1 row retrieved starting from 1 in 255 ms (execution: 3 ms, fetching: 252 ms)
   ```

   ```
   20 rows retrieved starting from 1 in 27 ms (execution: 3 ms, fetching: 24 ms)
   ```

   

   #### 结论

   本次实验通过在 `DataGrip`（PostgreSQL 引擎）与 `CS307-DB` 自研系统中进行对比测试，两者的效率变化与结果基本一致。验证了 B+ 树索引在本项目中的**正确性与高效性**。

   - 在 `CS307-DB` 中，未使用索引时对 `name = 'Zach_user7671'` 的等值查询耗时为 **84ms**，使用索引后耗时下降至 **低于1ms**，性能显著提升。
   - 对 `id BETWEEN 9980 AND 9999` 的范围查询，在建立索引后耗时从 **128ms** 大幅下降至 **4ms**，性能约提升了**30倍**，展示了 B+ 树在处理范围查询时的结构优势。
   - 在 `DataGrip` 中，未使用索引时对 `name = 'Zach_user7671'` 的等值查询耗时为 **307ms**，使用索引后耗时下降至 **255ms**，性能提升约 **17%**，符合预期。
   - 对 `id BETWEEN 9980 AND 9999` 的范围查询，在建立索引后耗时从 **254ms** 大幅下降至 **27ms**，展示了 B+ 树在处理范围查询时的结构优势。

   ------

   #### 补充说明

   尽管等值查询的提升幅度相对较小（52ms），这在实验规模仅为 10,000 行时是可以预期的。在此数据量级下，**内存访问与缓存命中**仍能保证 SeqScan 的可接受性能，导致索引优势未能完全体现。

   
