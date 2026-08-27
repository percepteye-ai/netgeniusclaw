//
//  NetClawWidgetBundle.swift
//  NetClawWidget
//
//  Created by John Capobianco on 8/15/26.
//

import WidgetKit
import SwiftUI

@main
struct NetClawWidgetBundle: WidgetBundle {
    var body: some Widget {
        NetClawWidget()
        NetClawWidgetControl()
    }
}
