/*
THIS FILE WAS AUTOGENERATED! DO NOT EDIT!
file to edit: 09_optimizer.ipynb

*/

import Path
import TensorFlow

//Expandable enum to have tab-complete and typo-proof for the hyper-param names
public struct HyperParams {
    public static let lr = "learningRate"
}

public protocol StatDelegate {
    var name: String {get}
    var defaultHPs: [String:Float] {get}
    
    func update(_ state: inout [String:TF], p: TF, 𝛁p: TF, hps: inout [String:Float])
}

public protocol StepDelegate {
    var defaultHPs: [String:Float] {get}
    
    func update(_ p: inout TF, 𝛁p: inout TF, state: [String:TF], hps: inout [String:Float])
}

public func mergeDicts(_ dicts: inout [[String:Float]], with newDict: [String:Float]) {
    for i in dicts.indices { 
        dicts[i].merge(newDict) { (_, new) in new } 
    }
}

public func mergeDicts(_ dicts: inout [[String:Float]], with newDicts: [[String:Float]]) {
    for i in dicts.indices { 
        dicts[i].merge(newDicts[i]) { (_, new) in new } 
    }
}

extension Dictionary where Value == Int{
    public init(mapFromArrays arrays: [[Key]]){
        self.init(uniqueKeysWithValues: arrays.enumerated().flatMap { i, arr in arr.map { ($0, i) } })
    }
}

//Why doesn't this work?
//extension Dictionary {
//    public init(constant: Value, keys: Array(Keys)){
//        self.init(uniqueKeysWithValues: keys.map { ($0, constant) })
//    }
//}

public func initState<Model: Layer>(for model: Model, names: [String]) 
-> [WritableKeyPath<Model.AllDifferentiableVariables, TF>: [String:TF]] {
    return [WritableKeyPath<Model.AllDifferentiableVariables, TF>: [String:TF]](
        uniqueKeysWithValues: model.variables.keyPaths.map { ($0, [String:TF](
            uniqueKeysWithValues: names.map { ($0, TF(0))}
        ))}
    )
}

public class StatefulOptimizer<Model: Layer>
    where Model.AllDifferentiableVariables == Model.CotangentVector {
    public typealias ModelKeyPath = WritableKeyPath<Model.AllDifferentiableVariables, TF>
    public typealias SplitDict = [ModelKeyPath: Int]
    public var hpGroups: [[String:Float]]
    public var splitDict: SplitDict
    public var states: [ModelKeyPath: [String: TF]]
    public var stats: [StatDelegate]
    public var steppers: [StepDelegate]
    public init(        
        for model: __shared Model,
        steppers: [StepDelegate],
        stats: [StatDelegate],
        hpGroups: [[String:Float]],
        splitArray: [[ModelKeyPath]]
    ) {
        self.hpGroups = Array(repeating: [:], count: hpGroups.count)
        (self.steppers,self.stats) = (steppers,stats)
        self.splitDict = SplitDict(mapFromArrays: splitArray)
        states = [:]
        steppers.forEach { mergeDicts(&self.hpGroups, with: $0.defaultHPs) }
        stats.forEach    { mergeDicts(&self.hpGroups, with: $0.defaultHPs) }
        states = initState(for: model, names: stats.map { $0.name })
        mergeDicts(&self.hpGroups, with: hpGroups)
    }
        
    public func update(
        _ model: inout Model.AllDifferentiableVariables,
        along direction: Model.CotangentVector
    ) {
        for kp in model.keyPaths {
            var 𝛁p = direction[keyPath: kp]
            var hps = hpGroups[splitDict[kp]!]
            stats.forEach() { $0.update(&states[kp]!, p: model[keyPath: kp], 𝛁p: 𝛁p, hps: &hps) }
            steppers.forEach() { $0.update(&model[keyPath: kp], 𝛁p: &𝛁p, state: states[kp]!, hps: &hps) }
            hpGroups[splitDict[kp]!] = hps
        }
    }
}

extension StatefulOptimizer: Optimizer{
    public var learningRate: Float {
        get { return hpGroups.last![HyperParams.lr]! } 
        set { 
            for i in hpGroups.indices {self.hpGroups[i][HyperParams.lr] = newValue }
        }
    }
    //For discriminative learning rates
    public var learningRates: [Float] {
        get { return hpGroups.map { $0[HyperParams.lr]! } }
        set { 
            for i in hpGroups.indices {self.hpGroups[i][HyperParams.lr] = newValue[i] } 
        }
    }
}

extension StatefulOptimizer{
    public convenience init (for model: __shared Model,
                             steppers: [StepDelegate],
                             stats: [StatDelegate],
                             hps: [String:Float]) {
        self.init(for: model,
                  steppers: steppers,
                  stats: stats,
                  hpGroups: [hps],
                  splitArray: [model.variables.keyPaths])
    }
}

public struct SGDStep: StepDelegate {
    public var defaultHPs: [String: Float] { return [HyperParams.lr: 3e-3] }
    public init() {}
    public func update(_ p: inout TF, 𝛁p: inout TF, state: [String:TF], hps: inout [String:Float]) {
        p -= 𝛁p * hps[HyperParams.lr]!
    }
}

public extension HyperParams {
    static let wd = "weightDecay"
}

public struct WeightDecay: StepDelegate {
    public var defaultHPs: [String: Float] { return [HyperParams.wd: 0] }
    public init() {}
    public func update(_ p: inout TF, 𝛁p: inout TF, state: [String:TF], hps: inout [String:Float]) {
        p *= 1 - hps[HyperParams.lr]! * hps[HyperParams.wd]!
    }
}

public struct L2Regularization: StepDelegate {
    public var defaultHPs: [String: Float] { return [HyperParams.wd: 0] }
    public init() {}
    public func update(_ p: inout TF, 𝛁p: inout TF, state: [String:TF], hps: inout [String:Float]) {
        𝛁p += hps[HyperParams.wd]! * p
    }
}

//Expandable enum to have tab completes/typo-proof for state variable names.
public struct StateKeys {
    public static let avgGrad = "averageGrad"
}

public extension HyperParams {
    static let mom = "momentum"
    static let momDamp = "dampening"
}

public struct AverageGrad: StatDelegate {
    public var defaultHPs: [String: Float] { return [HyperParams.mom: 0.9] }
    public let dampened: Bool
    public init(dampened: Bool = false) { self.dampened = dampened }
    public var name: String { return StateKeys.avgGrad }
    public func update(_ state: inout [String: TF], p: TF, 𝛁p: TF, hps: inout [String:Float]) {
        state[StateKeys.avgGrad]! *= hps[HyperParams.mom]!
        hps[HyperParams.momDamp] = 1.0 - (dampened ? hps[HyperParams.mom]! : 0.0)
        state[StateKeys.avgGrad]! += hps[HyperParams.momDamp]! * 𝛁p
    }
}

public struct MomentumStep: StepDelegate {
    public var defaultHPs: [String: Float] = [:]
    public init() {}
    public func update(_ p: inout TF, 𝛁p: inout TF, state: [String: TF], hps: inout [String:Float]) {
        p -= state[StateKeys.avgGrad]! * hps[HyperParams.lr]!
    }
}

public extension HyperParams {
    static let ²mom = "momentumSquares"
    static let ²momDamp = "dampeningSquares"
}

public extension StateKeys {
    static let avgSqr = "averageSquaredGrad"
}

public struct AverageSquaredGrad: StatDelegate {
    let dampened: Bool
    public init(dampened: Bool = true) { self.dampened = dampened }
    public var name: String { return StateKeys.avgSqr }
    public var defaultHPs: [String: Float] { return [HyperParams.²mom: 0.99] }
    public func update(_ state: inout [String: TF], p: TF, 𝛁p: TF, hps: inout [String:Float]) {
        state[StateKeys.avgSqr]! *= hps[HyperParams.²mom]!
        hps[HyperParams.²momDamp] = 1.0 - (dampened ? hps[HyperParams.²mom]! : 0.0)
        state[StateKeys.avgSqr]! += hps[HyperParams.²momDamp]! * 𝛁p.squared()
    }
}

public extension StateKeys {
    static let step = "stepCount"
}

public struct StepCount: StatDelegate {
    public var name: String { return StateKeys.step }
    public var defaultHPs: [String:Float] = [:]
    public init() {}
    public func update(_ state: inout [String: TF], p: TF, 𝛁p: TF, hps: inout [String:Float]) {
        state[StateKeys.step]! += 1.0
    }
}

//public struct Epsilon: HetDictKey { public static var defaultValue: Float = 1e-5 }
public extension HyperParams {
    static let eps = "epsilon"
}

public struct AdamStep: StepDelegate {
    public var defaultHPs: [String: Float] { return [HyperParams.eps: 1e-5] }
    public init() {}
    public func update(_ p: inout TF, 𝛁p: inout TF, state: [String: TF], hps: inout [String:Float]) {
        let step = state[StateKeys.step]!
        let (mom,damp) = (hps[HyperParams.mom]!,hps[HyperParams.momDamp]!)
        let debias1 = damp * (1 - pow(mom, step)) / (1 - mom)
        let num = debias1 * state[StateKeys.avgGrad]!
        
        let (²mom,²damp) = (hps[HyperParams.²mom]!,hps[HyperParams.²momDamp]!)
        let debias2 = ²damp * (1 - pow(²mom, step)) / (1 - ²mom)
        let denom = sqrt(state[StateKeys.avgSqr]!/debias2) + hps[HyperParams.eps]!
        
        p -= hps[HyperParams.lr]! * num / denom
    }
}

public func sgdOpt<Model>(lr: Float, mom: Float = 0.9, wd: Float = 0.0, dampening: Bool = false
                         ) -> ((Model) -> StatefulOptimizer<Model>) {
    var steppers: [StepDelegate] = (mom != 0) ? [MomentumStep()] : [SGDStep()]
    if wd != 0 { steppers.append(WeightDecay()) }
    let stats = (mom != 0) ? [AverageGrad(dampened: dampening)] : []
    var hps: [String: Float] = [HyperParams.lr: lr]
    if mom != 0 { hps[HyperParams.mom] = mom }
    if wd != 0  { hps[HyperParams.wd ] = wd  }
    return {model in 
        return StatefulOptimizer(for: model, steppers: steppers, stats: stats, hps: hps)}
}

public func adamOpt<Model>(lr: Float, mom: Float = 0.9, beta: Float=0.99, wd: Float = 0.0, eps: Float = 1e-5
                         ) -> ((Model) -> StatefulOptimizer<Model>) {
    var steppers: [StepDelegate] = [AdamStep()]
    if wd != 0 { steppers.append(WeightDecay()) }
    let stats: [StatDelegate] = [AverageGrad(dampened: true), AverageSquaredGrad(), StepCount()]
    var hps: [String: Float] = [HyperParams.lr: lr]
    hps[HyperParams.mom] = mom
    hps[HyperParams.²mom] = beta
    hps[HyperParams.eps] = eps
    if wd != 0  { hps[HyperParams.wd ] = wd  }
    return {model in 
        return StatefulOptimizer(for: model, steppers: steppers, stats: stats, hps: hps)}
}

public extension StatefulOptimizer {
    func setParam(_ hp: String, _ val: Float) {
        for i in 0..<hpGroups.count { hpGroups[i][hp] = val }
    }
}

extension Learner where Opt.Scalar: BinaryFloatingPoint, 
    Opt.Model.AllDifferentiableVariables == Opt.Model.CotangentVector{
    public class ParamScheduler: Delegate {
        public override var order: Int { return 1 }
        public typealias ScheduleFunc = (Float) -> Float

        // A learning rate schedule from step to float.
        public var scheduler: ScheduleFunc
        public let hp: String
        
        public init(scheduler: @escaping (Float) -> Float, hp: String) {
            (self.scheduler,self.hp) = (scheduler,hp)
        }
        
        override public func batchWillStart(learner: Learner) {
            let val = scheduler(learner.pctEpochs/Float(learner.epochCount))
            (learner.opt as! StatefulOptimizer<Opt.Model>).setParam(hp, val)
        }
    }
    
    public func makeParamScheduler(_ scheduler: @escaping (Float) -> Float, hp: String) -> ParamScheduler {
        return ParamScheduler(scheduler: scheduler, hp: hp)
    }
}

public func oneCycleSchedulers(_ lrMax: Float, pctStart:Float=0.25, divStart: Float = 10, divEnd: Float = 1e5, 
                               moms: (Float,Float,Float) = (0.95,0.85,0.95)) 
-> ((Float) -> Float, (Float) -> Float){
    let lrSched = combineSchedules(
        pcts: [pctStart, 1-pctStart], 
        schedules: [makeAnnealer(start: lrMax/divStart, end: lrMax, schedule: cosineSchedule),
                    makeAnnealer(start: lrMax, end: lrMax/divEnd, schedule: cosineSchedule)])
    let momSched = combineSchedules(
        pcts: [pctStart, 1-pctStart], 
        schedules: [makeAnnealer(start: moms.0, end: moms.1, schedule: cosineSchedule),
                    makeAnnealer(start: moms.1, end: moms.2, schedule: cosineSchedule)])
    return (lrSched, momSched)
}

extension Learner where Opt.Scalar: BinaryFloatingPoint, 
    Opt.Model.AllDifferentiableVariables == Opt.Model.CotangentVector{

    public func addOneCycleDelegates(_ lrMax: Float, pctStart:Float=0.25, divStart: Float = 10, divEnd: Float = 1e5, 
                               moms: (Float,Float,Float) = (0.95,0.85,0.95)) {
        let scheds = oneCycleSchedulers(lrMax, pctStart: pctStart, divStart: divStart, divEnd: divEnd, moms: moms)
        addDelegates([makeParamScheduler(scheds.0 , hp: HyperParams.lr), 
                      makeParamScheduler(scheds.1 , hp: HyperParams.mom)])
    }
}