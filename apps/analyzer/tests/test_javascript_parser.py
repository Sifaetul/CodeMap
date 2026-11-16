import pytest
from apps.analyzer.parsers.javascript_parser import JavaScriptParser

def test_javascript_parser_esm_and_classes():
    code = """
import React, { useState, useEffect as useMount } from 'react';
import * as utils from './utils';
import './globals.css';

export class OrderService extends BaseService {
    constructor() {
        super();
        this.init();
    }

    processOrder(order) {
        validate(order);
        saveOrder(order);
    }
}

export const calculateTax = (subtotal) => {
    return subtotal * 0.15;
};

export default function App() {
    const total = calculateTax(100);
    return render(total);
}
"""
    parser = JavaScriptParser()
    result = parser.parse(code, "App.tsx")
    
    # 1. Check Imports
    imports = result["imports"]
    assert len(imports) >= 4
    import_names = [i["name"] for i in imports]
    assert any("react.useState" in name for name in import_names)
    assert any("react.useMount" in name for name in import_names)
    assert any("./utils" in name for name in import_names)

    # 2. Check Entities
    entities = result["entities"]
    entity_names = [e["name"] for e in entities]
    assert "OrderService" in entity_names
    assert "calculateTax" in entity_names
    assert "App" in entity_names

    # Check Entity types
    order_svc = next(e for e in entities if e["name"] == "OrderService")
    assert order_svc["type"] == "class"
    assert order_svc["extends"] == "BaseService"

    app_func = next(e for e in entities if e["name"] == "App")
    assert app_func["type"] == "function"

    # 3. Check Calls
    calls = result["calls"]
    order_calls = [c["callee"] for c in calls if c["caller"] == "OrderService"]
    assert "validate" in order_calls or "init" in order_calls

    app_calls = [c["callee"] for c in calls if c["caller"] == "App"]
    assert "calculateTax" in app_calls
