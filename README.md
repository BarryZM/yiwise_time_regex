## Yiwise时间信息抽取模块（通用场景）：Yiwise Time Extractor

目前release的版本适用于**通用场景**下的时间挖掘，可通过参数`is_prefer_future`设置返回**未来**或**过去**的时间。

对话场景下的模块为：yiwise_time_dialogue，可通过`pip install yiwise_time_dialogue`下载使用，该场景下，优先返回**未来**的时间。

### Update

2019.11.14更新：

（1）统一了输出形式；

（2）将原`error`输出集成到`type`中，现在新增了`no_time_delta`和`no_time_stamp`两类。

2019.10.16更新：

（1）修复了`10月14日`、`2019年`不返回的错误；

（2）修复了部分`fuzzy_time`的返回错误。

2019.09.24更新：

（1）修复了`这周五`、`本周五`在不同倾向(future/past)下识别不同的bug；

（2）新增`周五`在不同倾向(future/past)下的识别（根据当前系统时间判断）。

2019.09.23更新：

（1）新增时间差表达：`三点过了一刻钟的样子吧`，`三点缺一分钟`等；

（2）修复0点和24点在不同倾向(future/past)下的bug；

（3）修复模糊匹配：`过去半个多小时了`、`十几分钟前`分别调整为`过去半个小时了`、`十分钟前`；

（4）新增模糊时间返回值：`is_fuzzy_time`。

## Installation
```
pip install yiwise-time-regex
```

## Quack Start
注：以下demo的测试时间为`2019-11-14 15:22:00`
```
>>> from yiwise_time_regex import TimeExtractor

>>> te_4_future = TimeExtractor(is_prefer_future=True)

>>> te_4_past = TimeExtractor(is_prefer_future=False)
```

### TimeDelta类型

支持如：半年后、一周前、三天半后、十分钟后等表述

```
>>> te_4_future.parse('半小时左右')

# 返回未来的时间点

'{"type": "time_stamp", "norm_time": ["2019-11-14 15:52:00"], "str_time": ["半小时"], "is_fuzzy_time": false}'

>>> te_4_past.parse('半小时左右')

# 返回过去的时间点

'{"type": "time_stamp", "norm_time": ["2019-11-14 14:52:00"], "str_time": ["半小时"], "is_fuzzy_time": false}'

```

### TimeStamp类型

支持如：明天七点、下下下周三早上十点一刻、大大大后天这时候、现在等表述

```
>>> te_4_future.parse('周五上午十点')

'{"type": "time_stamp", "norm_time": ["2019-11-15 10:00:00"], "str_time": ["周5上午10点"], "is_fuzzy_time": false}'

>>> te_4_past.parse('周五上午十点')

'{"type": "time_stamp", "norm_time": ["2019-11-08 10:00:00"], "str_time": ["周5上午10点"], "is_fuzzy_time": false}'

```

### TimeSpan类型

支持如：明天八点到十点、十点到两点等表述

```
>>> te_4_future.parse('十点到两点')

# 返回未来的时间点

'{"type": "time_span", "norm_time": ["2019-11-14 22:00:00", "2019-11-15 02:00:00"], "str_time": ["10点", "2点"], "is_fuzzy_time": false}'

>>> te_4_past.parse('十点到两点')

# 返回过去的时间点

'{"type": "time_span", "norm_time": ["2019-11-14 10:00:00", "2019-11-14 14:00:00"], "str_time": ["10点", "2点"], "is_fuzzy_time": false}'

```

**注意**
te_4_future和te_4_past的区别仅体现在非明确表达的时间上，如上述的`十点到两点`，或者`两点`这种模糊表达，对于明确表达时间的，如`明天早上八点到明天晚上十点`，二者返回结果相同；

目前对于多时间处理中的跨越当前时刻的处理结果不佳，如`十点到四点`，当前时刻为`2019-11-14 15:22:00`，无法返回以下结果：

`'{"type": "time_span", "norm_time": ["2019-11-14 10:00:00", "2019-11-14 16:00:00"], "str_time": ["10点", "4点"], "is_fuzzy_time": false}'`

**其中，10点为过去时间，而4点为未来时间。**

实际返回结果为：

```
>>> te_4_future.parse('十点到四点')

# 返回未来的时间点

'{"type": "time_span", "norm_time": ["2019-11-14 22:00:00", "2019-11-15 04:00:00"], "str_time": ["10点", "4点"], "is_fuzzy_time": false}'

>>> te_4_past.parse('十点到四点')

# 返回过去的时间点

'{"type": "time_span", "norm_time": ["2019-11-13 22:00:00", "2019-11-14 04:00:00"], "str_time": ["10点", "4点"], "is_fuzzy_time": false}'

```

