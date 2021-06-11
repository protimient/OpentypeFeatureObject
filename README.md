# OpentypeFeatureObject
This is a python module to convert Opentype Feature code (à la AFDKO) to python objects.
It is primarily used to subset the code to a specified script, language and/or glyph list.

Example Usage:
```python
import OpentypeFeatureObject

feature_code = """
feature xxxx {
  sub a by b;
  sub x by z;
} xxxx;
"""

feature_object = OpentypeFeatureObject.Feature(feature_code)
subset_feature = feature_object.subset('latn', ['a', 'b'])
subset_feature.write()
>>> feature xxxx {
...    sub a by b;
... } xxxx;
```
