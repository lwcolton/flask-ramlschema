pylint_output=`pylint -E flask_ramlschema | grep -v "An attribute defined in json.encoder line"`
pylint_errors=`echo "$pylint_output" | grep -vE '^\*.*'`
if [ -z "$pylint_errors" ]; then
    echo "Pylint passed"
else
    echo "Pylint failed!"
    echo "$pylint_output"
    exit 1
fi
